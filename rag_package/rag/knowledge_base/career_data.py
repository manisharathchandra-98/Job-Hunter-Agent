"""
Career knowledge base — role-specific skills, keywords, and resume guidance.
Used to populate the OpenSearch index for RAG grounding.
"""

CAREER_DOCUMENTS = [
    # ── BACKEND ENGINEER ───────────────────────────────────────────
    {
        "role": "Backend Engineer",
        "doc_type": "skills",
        "title": "Backend Engineer Core Skills",
        "content": """
Backend Engineers design and implement server-side systems, APIs, and databases.
Core technical skills: Python, Java, Node.js, Go, REST APIs, GraphQL, gRPC,
PostgreSQL, MySQL, MongoDB, Redis, Kafka, RabbitMQ, Docker, Kubernetes,
AWS Lambda, EC2, RDS, S3, microservices, distributed systems, system design,
data modeling, caching strategies, authentication (OAuth2, JWT), CI/CD,
unit testing, integration testing, performance optimization.
Soft skills: code review, technical documentation, cross-team collaboration.
        """,
        "keywords": ["REST API", "microservices", "PostgreSQL", "Redis", "Kafka",
                     "Docker", "Kubernetes", "Python", "Java", "Node.js", "Go",
                     "system design", "distributed systems", "gRPC", "GraphQL"]
    },
    {
        "role": "Backend Engineer",
        "doc_type": "resume_tips",
        "title": "Backend Engineer Resume Best Practices",
        "content": """
For backend roles, quantify system impact: 'Reduced API latency by 40% through Redis caching'
rather than 'improved performance'. Show scale: requests per second, data volume, user count.
Highlight: system design decisions, database optimization, scalability work.
Include: languages and frameworks used, cloud platforms (AWS/GCP/Azure), CI/CD tools.
Strong action verbs: Architected, Optimized, Reduced, Scaled, Refactored, Designed, Implemented.
Avoid: vague statements like 'worked on backend'; be specific about your contribution.
        """,
        "keywords": ["latency", "throughput", "scalability", "optimization", "architecture"]
    },

    # ── FRONTEND ENGINEER ──────────────────────────────────────────
    {
        "role": "Frontend Engineer",
        "doc_type": "skills",
        "title": "Frontend Engineer Core Skills",
        "content": """
Frontend Engineers build user interfaces and browser-based experiences.
Core technical skills: React, Vue, Angular, TypeScript, JavaScript (ES6+),
HTML5, CSS3, Tailwind CSS, SASS, Redux, Zustand, React Query, Next.js, Vite,
Webpack, REST APIs, GraphQL, unit testing (Jest, React Testing Library),
E2E testing (Playwright, Cypress), accessibility (WCAG 2.1), responsive design,
performance optimization (Core Web Vitals, lazy loading, code splitting),
version control (Git), Figma/design handoff, CI/CD.
        """,
        "keywords": ["React", "TypeScript", "Next.js", "Redux", "CSS", "Tailwind",
                     "Jest", "Cypress", "accessibility", "performance", "responsive design"]
    },
    {
        "role": "Frontend Engineer",
        "doc_type": "resume_tips",
        "title": "Frontend Engineer Resume Best Practices",
        "content": """
Showcase user impact: 'Improved Lighthouse performance score from 62 to 94'.
Mention component libraries built, design system contributions.
Quantify: page load time reductions, bundle size improvements, conversion rate lifts.
Include: frameworks, state management libraries, testing tools, accessibility work.
Link to portfolio/GitHub with live demos — essential for frontend roles.
Strong verbs: Built, Designed, Optimized, Migrated, Implemented, Reduced, Improved.
        """,
        "keywords": ["Core Web Vitals", "Lighthouse", "bundle size", "component library", "design system"]
    },

    # ── FULL STACK ENGINEER ────────────────────────────────────────
    {
        "role": "Full Stack Engineer",
        "doc_type": "skills",
        "title": "Full Stack Engineer Core Skills",
        "content": """
Full Stack Engineers work across the entire application stack.
Frontend: React, Vue, Next.js, TypeScript, HTML, CSS.
Backend: Node.js, Python, Java, REST APIs, GraphQL.
Databases: PostgreSQL, MongoDB, Redis.
Cloud: AWS (EC2, Lambda, RDS, S3), Docker, Kubernetes.
DevOps: CI/CD, GitHub Actions, Linux, Nginx.
Testing: Jest, Pytest, Selenium.
Key strength: ability to own features end-to-end, from UI to database schema to API design.
        """,
        "keywords": ["full stack", "end-to-end", "React", "Node.js", "PostgreSQL",
                     "AWS", "Docker", "TypeScript", "REST API"]
    },

    # ── DATA SCIENTIST ────────────────────────────────────────────
    {
        "role": "Data Scientist",
        "doc_type": "skills",
        "title": "Data Scientist Core Skills",
        "content": """
Data Scientists extract insights from data and build predictive models.
Core skills: Python (NumPy, Pandas, Scikit-learn), R, SQL, machine learning
(supervised/unsupervised), deep learning (TensorFlow, PyTorch), NLP,
feature engineering, statistical analysis, A/B testing, hypothesis testing,
data visualization (Matplotlib, Seaborn, Tableau, Power BI),
big data (Spark, Hadoop), cloud ML (AWS SageMaker, GCP Vertex AI),
experiment design, model deployment (MLflow, FastAPI), Jupyter notebooks.
        """,
        "keywords": ["Python", "Machine Learning", "SQL", "TensorFlow", "PyTorch",
                     "Pandas", "Scikit-learn", "A/B testing", "SageMaker", "NLP",
                     "statistical analysis", "feature engineering"]
    },
    {
        "role": "Data Scientist",
        "doc_type": "resume_tips",
        "title": "Data Scientist Resume Best Practices",
        "content": """
Lead with impact metrics: 'Built churn prediction model achieving 87% accuracy, reducing churn by 15%'.
Show the full ML lifecycle: data collection, EDA, feature engineering, modeling, deployment, monitoring.
Mention datasets size (millions of rows, terabytes) to show you work at scale.
Include: Kaggle rankings, published papers, open-source contributions, competition results.
Separate sections for: Technical Skills, Projects, Experience.
Strong verbs: Developed, Trained, Deployed, Analyzed, Predicted, Reduced, Increased.
        """,
        "keywords": ["accuracy", "precision", "recall", "AUC-ROC", "F1", "model deployment", "MLOps"]
    },

    # ── ML ENGINEER ───────────────────────────────────────────────
    {
        "role": "Machine Learning Engineer",
        "doc_type": "skills",
        "title": "ML Engineer Core Skills",
        "content": """
ML Engineers build and deploy production machine learning systems.
Core skills: Python, PyTorch, TensorFlow, Keras, model optimization (quantization, pruning),
MLOps (MLflow, Kubeflow, Weights & Biases), feature stores (Feast), data pipelines,
Docker, Kubernetes, REST API for model serving, ONNX, TensorRT, SageMaker,
Vertex AI, distributed training, LLMs and fine-tuning, vector databases
(Pinecone, Weaviate, OpenSearch), RAG pipelines, prompt engineering.
        """,
        "keywords": ["MLOps", "PyTorch", "model deployment", "feature store", "distributed training",
                     "LLM", "RAG", "vector database", "SageMaker", "Kubeflow"]
    },

    # ── DEVOPS / SRE ──────────────────────────────────────────────
    {
        "role": "DevOps Engineer",
        "doc_type": "skills",
        "title": "DevOps / SRE Core Skills",
        "content": """
DevOps Engineers and SREs build and maintain infrastructure and deployment pipelines.
Core skills: AWS (EC2, EKS, ECS, RDS, S3, CloudFormation, CDK), Terraform, Ansible,
Docker, Kubernetes, Helm, CI/CD (GitHub Actions, Jenkins, GitLab CI, CircleCI),
monitoring (Prometheus, Grafana, Datadog, CloudWatch), logging (ELK Stack),
incident management, SLOs/SLAs/SLIs, Linux administration, Bash/Python scripting,
networking (VPC, subnets, load balancers, DNS), security (IAM, secrets management).
        """,
        "keywords": ["Terraform", "Kubernetes", "Docker", "CI/CD", "AWS", "monitoring",
                     "Prometheus", "Grafana", "SRE", "infrastructure as code", "Helm"]
    },
    {
        "role": "DevOps Engineer",
        "doc_type": "resume_tips",
        "title": "DevOps Resume Best Practices",
        "content": """
Quantify reliability: 'Maintained 99.95% uptime across 200-service microservices platform'.
Show cost savings: 'Reduced AWS infrastructure cost by 30% through spot instance optimization'.
Highlight automation: percentage of manual processes automated, deployment frequency improvements.
Include: tools and platforms used, scale of infrastructure managed, incident response experience.
Certifications matter: AWS Solutions Architect, CKA (Kubernetes), HashiCorp Terraform Associate.
Strong verbs: Automated, Reduced, Deployed, Monitored, Scaled, Migrated, Implemented.
        """,
        "keywords": ["uptime", "deployment frequency", "MTTR", "infrastructure as code",
                     "cost optimization", "incident response", "SLO"]
    },

    # ── CLOUD ENGINEER ────────────────────────────────────────────
    {
        "role": "Cloud Engineer",
        "doc_type": "skills",
        "title": "Cloud Engineer Core Skills",
        "content": """
Cloud Engineers design and implement cloud architecture solutions.
AWS services: VPC, EC2, Lambda, ECS/EKS, RDS, DynamoDB, S3, CloudFront,
API Gateway, Cognito, IAM, KMS, CloudTrail, CloudWatch, SNS, SQS, Step Functions.
IaC: Terraform, AWS CDK, CloudFormation.
Networking: VPC design, subnets, security groups, Transit Gateway, Direct Connect.
Security: least-privilege IAM, encryption at rest/in transit, compliance (SOC2, HIPAA).
Cost management: Reserved Instances, Savings Plans, right-sizing.
Certifications: AWS Solutions Architect (Associate/Professional), AWS DevOps Engineer.
        """,
        "keywords": ["AWS", "VPC", "Lambda", "EKS", "Terraform", "CDK", "CloudFormation",
                     "IAM", "cost optimization", "Solutions Architect"]
    },

    # ── GENERAL RESUME ADVICE ─────────────────────────────────────
    {
        "role": "General",
        "doc_type": "resume_strategy",
        "title": "Universal Resume Strategy for Tech Roles",
        "content": """
ATS optimization: mirror keywords from the job description exactly.
Quantify everything: numbers, percentages, scale, time saved, money saved.
Use the STAR format for experience bullets: Situation, Task, Action, Result.
Summary section should be 2-3 lines tailored to each specific role.
Skills section: group by category (Languages, Frameworks, Cloud, Tools).
Keep to 1-2 pages; use white space effectively.
File format: PDF for direct applications, Word for recruiter submissions.
Action verbs by category:
  - Leadership: Led, Managed, Mentored, Directed, Coordinated
  - Technical: Architected, Engineered, Implemented, Developed, Designed
  - Impact: Reduced, Increased, Improved, Accelerated, Optimized, Saved
  - Collaboration: Partnered, Collaborated, Facilitated, Presented
        """,
        "keywords": ["ATS", "STAR method", "quantify", "action verbs", "tailored",
                     "keywords", "summary", "skills section"]
    },
    {
        "role": "General",
        "doc_type": "interview_prep",
        "title": "Tech Resume Red Flags to Avoid",
        "content": """
Avoid these resume mistakes that get screened out:
1. Generic objective statements ('Looking for a challenging role...')
2. Listing technologies without showing how you used them
3. Job descriptions that read like responsibilities, not achievements
4. Missing dates on employment history
5. Unexplained employment gaps
6. First-person pronouns (I, my, we)
7. Unprofessional email addresses
8. Outdated technologies listed prominently (e.g. Flash, SOAP, SVN)
9. Inconsistent formatting and font sizes
10. Spelling and grammar errors — proofread everything
        """,
        "keywords": ["red flags", "ATS screening", "achievements", "accomplishments"]
    },

    # ── ML / AI ENGINEER (from real JD) ───────────────────────────────────
    {
        "role": "ML/AI Engineer",
        "doc_type": "skills",
        "title": "ML/AI Engineer Core Technical Skills",
        "content": """
ML/AI Engineers design, build, and deploy production GenAI applications and pipelines.

Backend Engineering:
Python with AsyncIO, Pydantic, REST API development. Strong software engineering
fundamentals — clean code, testing, performance optimization.

Containerization & Serverless:
Docker build experience specifically for serverless containers (AWS Lambda container images,
ECS Fargate). Multi-stage builds, image optimization, ECR.

API & Gateway Architecture:
Building API client adapters for internal/corporate gateways. Authentication patterns:
OAuth2, API keys, mTLS, AWS SigV4. Designing robust API wrappers around LLM providers
(Azure OpenAI gateway, AWS Bedrock, OpenAI API).

Cloud Infrastructure (AWS):
ECS (Fargate), IAM (least-privilege roles and policies), API Gateway, VPC (subnets,
security groups, NAT), Secrets Manager, Lambda, S3, DynamoDB, CloudWatch.

Infrastructure as Code:
Terraform or AWS CDK for reproducible infrastructure. Modular design, state management,
environment separation (dev/staging/prod).

LLM Integration:
Azure OpenAI integration and gateway configuration. AWS Bedrock (Claude, Titan).
OpenAI API. Prompt construction, token management, streaming responses, error handling,
retry logic and rate limit handling.

Agent Frameworks:
STRANDS, LangChain, LlamaIndex — agent orchestration, tool creation, MCP (Model Context
Protocol) integration. Multi-agent architectures, tool calling, memory management.

Vector & RAG:
RAG pipeline design and implementation. Vector databases: Pinecone, FAISS, Weaviate,
Amazon OpenSearch. Embedding models (OpenAI Ada, Titan, BGE). Chunking strategies,
metadata filtering, hybrid search, re-ranking.

GenAI Lifecycle:
Foundation model fine-tuning (LoRA, QLoRA, PEFT). Prompt engineering strategies:
chain-of-thought, few-shot, ReAct. Evaluation: bias detection, hallucination monitoring,
accuracy metrics. Model deployment on AWS, Azure, GCP.
        """,
        "keywords": [
            "Python", "AsyncIO", "Pydantic", "REST API", "Docker", "serverless containers",
            "ECS", "IAM", "API Gateway", "VPC", "Secrets Manager", "Terraform", "AWS CDK",
            "Azure OpenAI", "LLM", "STRANDS", "LangChain", "LlamaIndex", "RAG",
            "vector database", "Pinecone", "FAISS", "Weaviate", "OpenSearch",
            "fine-tuning", "prompt engineering", "GenAI", "agent framework",
            "MCP", "embeddings", "GPT", "Claude", "LLaMA"
        ]
    },
    {
        "role": "ML/AI Engineer",
        "doc_type": "resume_tips",
        "title": "ML/AI Engineer Resume Best Practices",
        "content": """
For ML/AI Engineer roles, the resume must demonstrate both strong software engineering
AND AI/ML depth — many candidates have one but not both.

Backend Engineering Evidence:
Show production-grade Python: mention AsyncIO for concurrent workloads, Pydantic for
data validation, and REST API design patterns. Quantify scale: requests/second, latency,
data volume processed.

RAG Pipeline Specifics:
Don't just say 'built RAG system'. Specify: chunking strategy used, embedding model,
vector store, retrieval method (semantic/hybrid/keyword), re-ranking approach, and
accuracy or latency improvement achieved.
Example: 'Built RAG pipeline using LangChain + Weaviate with hybrid search, reducing
hallucination rate by 35% vs. vanilla LLM baseline.'

Agent Framework Experience:
Name the specific framework (STRANDS, LangChain, LlamaIndex). Describe tools created,
MCP integrations, and how the agent was evaluated or monitored in production.

LLM Integration:
Mention specific providers (Azure OpenAI gateway, AWS Bedrock, OpenAI API). Show you
understand gateway patterns, authentication, token optimization, and cost management.

Infrastructure Proof:
Hiring managers want engineers who can own the full stack. Show Docker + ECS/Lambda
deployment, Terraform/CDK for IaC, and IAM policy design.

Monitoring & Safety:
Explicitly mention hallucination monitoring, bias evaluation, and output validation
pipelines — this differentiates senior engineers from junior ones.

Strong action verbs: Architected, Deployed, Fine-tuned, Integrated, Optimized,
Reduced, Built, Designed, Implemented, Evaluated, Monitored.
        """,
        "keywords": [
            "RAG pipeline", "hallucination", "fine-tuning", "agent", "tool creation",
            "vector store", "hybrid search", "re-ranking", "AsyncIO", "serverless",
            "LLM gateway", "prompt engineering", "evaluation", "bias monitoring",
            "production ML", "MLOps", "model serving"
        ]
    },
    {
        "role": "ML/AI Engineer",
        "doc_type": "jd_reference",
        "title": "ML/AI Engineer Sample Job Description (Reference)",
        "content": """
This is a real job description used as RAG grounding for ML/AI Engineer roles.

Required skills:
- Python backend engineering with AsyncIO, Pydantic, REST API development
- Containerization with Docker, specifically serverless container builds
- API client architecture for internal/corporate gateways and authentication
- AWS: ECS, IAM, API Gateway, VPC, Secrets Manager
- Terraform or AWS CDK infrastructure as code
- LLM integration with Azure OpenAI / corporate AI gateway
- Agent framework experience: STRANDS, LangChain, or LlamaIndex for agent builds,
  tool creation, and Model Context Protocol (MCP)
- Vector database and RAG experience

Responsibilities:
- Design and develop GenAI applications using LLMs (GPT, Claude, LLaMA)
- Build Retrieval Augmented Generation (RAG) pipelines
- Fine-tune foundation models as needed
- Develop prompt engineering strategies for business use cases
- Deploy AI solutions on cloud platforms (AWS, Azure, GCP)
- Implement and manage vector databases: Pinecone, FAISS, Weaviate
- Integrate GenAI APIs into enterprise applications
- Ensure model performance, scalability, and security
- Monitor AI outputs for bias, hallucination, and accuracy

Key differentiators hiring managers look for:
- Production RAG systems (not just demos)
- Agent orchestration with real tool integrations
- LLM gateway and cost optimization experience
- End-to-end ownership: from prompt to infrastructure to monitoring
        """,
        "keywords": [
            "STRANDS", "LangChain", "LlamaIndex", "Azure OpenAI", "LLM gateway",
            "Pinecone", "FAISS", "Weaviate", "fine-tuning", "prompt engineering",
            "RAG", "GenAI", "MCP", "tool creation", "ECS", "Terraform", "AsyncIO"
        ]
    },
]

