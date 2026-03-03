# Job Fit Analyzer

> AI-powered career intelligence platform that scores resume-to-job-description fit and generates targeted resume improvement suggestions using a multi-agent serverless pipeline on AWS.

---

## What It Does

Paste a resume and a job description. The platform runs both through a 6-agent AI pipeline and returns:

- **Fit score** — quantified match percentage across skills, experience, and role requirements
- **Skill gap analysis** — exactly what's missing and how critical each gap is
- **Salary benchmark** — where the role sits in the market based on your experience level
- **Difficulty rating** — how competitive this role is to land
- **Resume coaching** — 8 categories of specific, actionable improvement suggestions grounded in the actual job description

---

## Architecture

```
User (React) → API Gateway → Lambda Proxy → Step Functions
                                                    │
                    ┌───────────────────────────────┤
                    ▼                               ▼
             ParseJob Agent                  EstimateSkills Agent
             (extract JD data)               (Bedrock: identify required skills)
                    │
                    ▼
             EmbedResume Agent
             (Bedrock Titan: semantic similarity)
                    │
                    ▼
             MatchSkills Agent
             (difficulty score + weighted match %)
                    │
                    ▼
             AggregateResults Agent
             (DynamoDB: combine all outputs)
                    │
                    ▼
             ResumeCoach Agent ←── RAG (S3 vector index + Bedrock Titan)
             (Bedrock Claude 3 Haiku: 8-category suggestions)
                    │
                    ▼
             DynamoDB (status: completed)
                    │
                    ▼
             React Frontend (poll → render results)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | AWS Step Functions |
| Compute | AWS Lambda (Python 3.11) |
| LLM | Amazon Bedrock — Claude 3 Haiku |
| Embeddings | Amazon Bedrock — Titan Embed Text v1 |
| Database | Amazon DynamoDB |
| API | Amazon API Gateway (REST + API key auth) |
| Frontend | React + Vite + Tailwind CSS |
| CDN | AWS CloudFront + S3 |
| RAG Store | Amazon S3 (JSON vector index) |
| Infrastructure | AWS CDK (Python) |
| CI/CD | GitHub Actions |

---

## Agent Pipeline

| # | Agent | Lambda Function | Responsibility |
|---|---|---|---|
| 1 | ParseJob | `job-analyzer-agent-parser` | Extract structured data from job description |
| 2 | EstimateSkills | `job-analyzer-agent-skills` | Identify required skills via Bedrock |
| 3 | EmbedResume | `job-analyzer-agent-gaps` | Semantic similarity scoring |
| 4 | MatchSkills | `job-analyzer-agent-difficulty` | Difficulty score + weighted match % |
| 5 | AggregateResults | `job-analyzer-agent-aggregator` | Combine outputs into DynamoDB |
| 6 | ResumeCoach | `job-analyzer-agent-resume-coach` | RAG-grounded resume suggestions |

---

## Resume Coach Output

The Resume Coach generates 8 structured improvement categories:

1. **ScoreProjection** — current score, projected score after changes, confidence level
2. **PriorityChanges** — top 3 highest-impact changes ranked by effort vs. impact
3. **KeywordsToAdd** — exact keywords from the JD missing from the resume, with context on where to add them
4. **BulletRewrites** — existing resume bullets rewritten with metrics and JD-aligned language
5. **NewBullets** — entirely new bullet points to add based on identified gaps
6. **SummaryRewrite** — full professional summary rewritten for the target role
7. **SkillsSectionRewrite** — updated skills section with missing keywords incorporated
8. **OverallStrategy** — high-level positioning advice for the application

---

## RAG Knowledge Base

The Resume Coach is grounded by a 16-document career knowledge base covering 8 engineering roles:

- Backend Engineer, Frontend Engineer, Full Stack Engineer
- Data Scientist, ML Engineer, DevOps / SRE, Cloud Engineer
- **ML/AI Engineer** (includes real job description with AsyncIO, STRANDS, LangChain, LlamaIndex, Azure OpenAI gateway, FAISS, Weaviate, Pinecone, MCP)

Documents are embedded with Amazon Bedrock Titan (1536 dimensions) and stored as a JSON vector index in S3. Retrieval uses in-memory cosine similarity search — no OpenSearch required.

---

## Project Structure

```
job-analyzer/
├── agents/
│   ├── aggregator/         # Agent 5 — combines results
│   ├── resume_coach/       # Agent 6 — resume suggestions
│   ├── agent3_salary/      # Salary benchmarking
│   ├── agent4_difficulty/  # Difficulty scoring
│   └── agent5_gaps/        # Gap analysis
├── api/
│   └── lambda_proxy.py     # API Gateway handler
├── frontend/
│   └── src/
│       └── components/
│           ├── SubmitForm.jsx
│           ├── MatchResults.jsx
│           └── ResumeSuggestions.jsx
├── infrastructure/         # AWS CDK stacks
├── rag/
│   ├── retriever.py        # S3-based cosine similarity retriever
│   ├── opensearch_client.py
│   ├── embeddings.py
│   └── knowledge_base/
│       ├── career_data.py  # 16 career documents
│       └── build_index.py  # Embed + upload to S3
├── scripts/
│   └── seed_data.py        # DynamoDB seed data
├── step_functions/         # State machine definition
├── tests/                  # pytest unit tests
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions CI/CD
└── pyproject.toml          # Poetry dependencies
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/match` | Submit resume + JD, returns `match_id` |
| `GET` | `/match/{id}` | Poll for results by match ID |
| `GET` | `/matches` | List all matches |
| `GET` | `/health` | Health check |
| `DELETE` | `/match/{id}` | Delete a match record |

All endpoints require `x-api-key` header.

---

## Setup & Deployment

### Prerequisites

- AWS CLI configured (`aws configure`)
- Node.js 18+ and Python 3.11+
- AWS CDK (`npm install -g aws-cdk`)
- Poetry (`pip install poetry`)

### 1. Install dependencies

```bash
poetry install --no-root
cd frontend && npm install
```

### 2. Deploy infrastructure

```bash
cd infrastructure
cdk bootstrap aws://<ACCOUNT_ID>/us-east-1
cdk deploy --all --require-approval never
```

### 3. Seed data

```bash
python scripts/seed_data.py
```

### 4. Build RAG index

```bash
python rag/knowledge_base/build_index.py
```

### 5. Deploy frontend

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://<FRONTEND_BUCKET>/ --delete
aws cloudfront create-invalidation --distribution-id <CF_ID> --paths "/*"
```

---

## CI/CD Pipeline

GitHub Actions workflow with **path-based change detection** — only changed components deploy:

| Changed Path | Job Triggered |
|---|---|
| `agents/aggregator/**` | Deploy Aggregator Lambda |
| `agents/resume_coach/**, rag/**` | Deploy Resume Coach Lambda (+ RAG layer) |
| `api/**` | Deploy API Proxy Lambda |
| `frontend/**` | Build + S3 sync + CloudFront invalidation |
| `infrastructure/**` | CDK deploy all stacks |
| `step_functions/**` | Update state machine definition |

### Required GitHub Secrets

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_ACCOUNT_ID
S3_BUCKET_NAME
CLOUDFRONT_DISTRIBUTION_ID
VITE_API_URL
VITE_API_KEY
RAG_INDEX_BUCKET
```

---

## Environment Variables

### Resume Coach Lambda

| Variable | Value |
|---|---|
| `MATCHES_TABLE_NAME` | `Matches` |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-haiku-20240307-v1:0` |
| `RAG_INDEX_BUCKET` | `job-analyzer-rag-<account-id>` |
| `RAG_INDEX_KEY` | `rag/career_index.json` |
| `USE_RAG` | `true` |

---

## DynamoDB Tables

| Table | Purpose |
|---|---|
| `Matches` | Match results, status, resume suggestions |
| `Candidates` | Candidate profiles |
| `Jobs` | Job postings |
| `SalaryData` | Salary benchmarks by role and level |
| `SkillsTaxonomy` | Skill categories and relationships |

---

## Development

### Run tests

```bash
poetry run pytest tests/ -v --tb=short
```

### Run locally (Lambda proxy)

```bash
cd api
python lambda_proxy.py
```

---

## Built With

- [Amazon Bedrock](https://aws.amazon.com/bedrock/) — Claude 3 Haiku + Titan Embeddings
- [AWS Step Functions](https://aws.amazon.com/step-functions/) — Agent orchestration
- [AWS CDK](https://aws.amazon.com/cdk/) — Infrastructure as code
- [React](https://react.dev/) — Frontend
- [GitHub Actions](https://github.com/features/actions) — CI/CD

---

## Author

**Mani Sharath Chandra**

---

*Built over 7 days — Days 1 through 7 — as a hands-on ML/AI engineering project.*