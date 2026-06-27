"""Seeds Neo4j AuraDB with AI vendor competitive graph and investor relationships."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

SEED_FILE = Path(__file__).parent.parent / "collector" / "seed_companies.json"

# Competitive pairs (bidirectional)
COMPETES_WITH_PAIRS = [
    ("Anthropic", "OpenAI"),
    ("Anthropic", "Cohere"),
    ("Anthropic", "Mistral"),
    ("OpenAI", "Cohere"),
    ("OpenAI", "Mistral"),
    ("OpenAI", "Inflection AI"),
    ("Cohere", "Mistral"),
    ("Cohere", "Writer"),
    ("Pinecone", "Weaviate"),
    ("Pinecone", "Qdrant"),
    ("Pinecone", "Chroma"),
    ("Pinecone", "Milvus"),
    ("Weaviate", "Qdrant"),
    ("Weaviate", "Chroma"),
    ("Qdrant", "Chroma"),
    ("LangChain", "LlamaIndex"),
    ("Replit", "Codeium"),
    ("Replit", "Tabnine"),
    ("Codeium", "Tabnine"),
    ("Weights and Biases", "Anyscale"),
    ("Scale AI", "Databricks"),
    ("Databricks", "Snowflake"),
]

# Investor → companies relationships
INVESTOR_BACKED_BY = {
    "Andreessen Horowitz": ["Mistral", "Anyscale"],
    "Google": ["Anthropic", "Cohere", "Mistral"],
    "Amazon": ["Anthropic"],
    "Microsoft": ["OpenAI", "Inflection AI"],
    "Sequoia": ["Harvey", "Perplexity", "Mistral"],
    "Spark Capital": ["Notion", "Weights and Biases"],
    "Lightspeed": ["Replit", "Grammarly"],
    "Index Ventures": ["Weaviate", "Qdrant"],
}


def seed() -> None:
    """Load seed data into Neo4j."""
    uri = os.getenv("NEO4J_URI", "").strip()
    user = os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()

    if not all([uri, user, password]):
        raise EnvironmentError(
            "NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in .env"
        )

    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Load seed companies
    with open(SEED_FILE) as f:
        all_companies = json.load(f)

    company_names = {c["name"] for c in all_companies}

    print("Seeding Neo4j graph...\n")

    # Create Company nodes
    print(f"Creating {len(all_companies)} Company nodes...")
    with driver.session() as session:
        for company in all_companies:
            session.run(
                """
                MERGE (c:Company {name: $name})
                ON CREATE SET
                  c.ticker = $ticker,
                  c.stage = $stage,
                  c.founded_year = $founded_year,
                  c.github_org = $github_org
                """,
                name=company["name"],
                ticker=company.get("ticker"),
                stage=company.get("stage"),
                founded_year=company.get("founded_year"),
                github_org=company.get("github_org"),
            )

    # Create COMPETES_WITH relationships
    competes_count = 0
    print("Creating COMPETES_WITH relationships...")
    with driver.session() as session:
        for company_a, company_b in COMPETES_WITH_PAIRS:
            # Only create if both companies exist in seed
            if company_a in company_names and company_b in company_names:
                session.run(
                    """
                    MATCH (a:Company {name: $company_a}), (b:Company {name: $company_b})
                    MERGE (a)-[:COMPETES_WITH]-(b)
                    """,
                    company_a=company_a,
                    company_b=company_b,
                )
                competes_count += 1

    # Create Investor nodes and BACKED_BY relationships
    investor_count = 0
    backed_by_count = 0
    print("Creating Investor nodes and BACKED_BY relationships...")
    with driver.session() as session:
        for investor, companies in INVESTOR_BACKED_BY.items():
            # Create investor node
            session.run(
                "MERGE (i:Investor {name: $name})",
                name=investor,
            )
            investor_count += 1

            # Create BACKED_BY relationships
            for company in companies:
                if company in company_names:
                    session.run(
                        """
                        MATCH (i:Investor {name: $investor}), (c:Company {name: $company})
                        MERGE (c)-[:BACKED_BY]->(i)
                        """,
                        investor=investor,
                        company=company,
                    )
                    backed_by_count += 1

    driver.close()

    print(f"\nSeeding complete:")
    print(f"  Company nodes: {len(all_companies)}")
    print(f"  Investor nodes: {investor_count}")
    print(f"  COMPETES_WITH relationships: {competes_count}")
    print(f"  BACKED_BY relationships: {backed_by_count}")


def verify() -> None:
    """Run verification queries and print results."""
    uri = os.getenv("NEO4J_URI", "").strip()
    user = os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()

    if not all([uri, user, password]):
        raise EnvironmentError(
            "NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in .env"
        )

    driver = GraphDatabase.driver(uri, auth=(user, password))

    print("\n" + "=" * 60)
    print("Verification Queries")
    print("=" * 60)

    with driver.session() as session:
        # All competitors of Anthropic
        print("\n1. Competitors of Anthropic:")
        result = session.run(
            """
            MATCH (a:Company {name: 'Anthropic'})-[:COMPETES_WITH]-(c:Company)
            RETURN c.name AS competitor
            ORDER BY competitor
            """
        )
        competitors = [record["competitor"] for record in result]
        for competitor in competitors:
            print(f"   - {competitor}")
        if not competitors:
            print("   (none)")

        # All companies backed by Google
        print("\n2. Companies backed by Google:")
        result = session.run(
            """
            MATCH (c:Company)-[:BACKED_BY]->(i:Investor {name: 'Google'})
            RETURN c.name AS company
            ORDER BY company
            """
        )
        google_backed = [record["company"] for record in result]
        for company in google_backed:
            print(f"   - {company}")
        if not google_backed:
            print("   (none)")

        # Companies with no competitors
        print("\n3. Companies with no competitors in graph:")
        result = session.run(
            """
            MATCH (c:Company)
            WHERE NOT (c)-[:COMPETES_WITH]-()
            RETURN c.name AS company
            ORDER BY company
            LIMIT 10
            """
        )
        no_competitors = [record["company"] for record in result]
        for company in no_competitors[:10]:
            print(f"   - {company}")
        if len(no_competitors) > 10:
            print(f"   ... and {len(no_competitors) - 10} more")
        if not no_competitors:
            print("   (none)")

        # Total relationship count
        print("\n4. Relationship counts:")
        result = session.run(
            """
            MATCH ()-[r]->()
            RETURN type(r) AS relationship_type, count(r) AS count
            """
        )
        for record in result:
            print(f"   {record['relationship_type']}: {record['count']}")

    driver.close()


def run() -> None:
    """Seed graph and verify."""
    seed()
    verify()


if __name__ == "__main__":
    run()
