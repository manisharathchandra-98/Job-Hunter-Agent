import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("Matches")
resp = table.scan()
items = resp.get("Items", [])
print(f"Total items in Matches: {len(items)}")

for item in items[-3:]:
    print(f"\n  match_id   : {item.get('match_id', 'N/A')}")
    print(f"  status     : {item.get('status', 'N/A')}")
    print(f"  rag_enabled: {item.get('rag_enabled', 'NOT SET')}")