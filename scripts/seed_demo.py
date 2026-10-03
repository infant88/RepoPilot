import os
import asyncio
import httpx

API_BASE = "http://localhost:8000/api"

async def seed_demo():
    print("Connecting to RepoPilot API at", API_BASE)
    sample_dir = os.path.join(os.getcwd(), "examples", "sample-repo")
    print(f"Registering demo repository from: {sample_dir}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Register demo repo
        res = await client.post(f"{API_BASE}/repositories", json={"url": sample_dir, "branch": "main"})
        if res.status_code != 200:
            print("Failed to register repo:", res.text)
            return

        repo = res.json()
        repo_id = repo["id"]
        print(f"Registered repository ID: {repo_id}, status: {repo['status']}")

        # 2. Poll until indexing is completed
        for _ in range(30):
            await asyncio.sleep(1)
            status_res = await client.get(f"{API_BASE}/repositories/{repo_id}/index-status")
            status_data = status_res.json()
            print(f"Indexing progress: {status_data['progress_percentage']}% - {status_data['status']}")
            if status_data["status"] == "COMPLETED":
                print(f"Repository indexed successfully! Indexed {status_data['total_files']} files, {status_data['total_chunks']} chunks.")
                break

        # 3. Run Benchmark Evaluation
        print("\nRunning RAG benchmark evaluation...")
        eval_res = await client.post(f"{API_BASE}/evaluations/run", json={"repository_id": repo_id})
        if eval_res.status_code == 200:
            eval_data = eval_res.json()
            print(f"Benchmark Results:")
            print(f"- Context Precision: {eval_data['context_precision'] * 100:.1f}%")
            print(f"- Context Recall:    {eval_data['context_recall'] * 100:.1f}%")
            print(f"- Faithfulness:       {eval_data['faithfulness'] * 100:.1f}%")
            print(f"- Answer Relevance:   {eval_data['answer_relevance'] * 100:.1f}%")
            print(f"- Total Latency:      {eval_data['total_latency_ms']} ms")
        else:
            print("Evaluation notice:", eval_res.text)

if __name__ == "__main__":
    asyncio.run(seed_demo())
