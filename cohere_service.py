import cohere

co = cohere.ClientV2()
MODEL="command-r-plus-08-2024"

def chat(query:str,) -> str:
    message = [{"role": "user", "content": query}]
    kwargs={"model":MODEL,"messages":message}
    response = co.chat(**kwargs)
    print(response)
    return "Completed"

chat("who are you?")
