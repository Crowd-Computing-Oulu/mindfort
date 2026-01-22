from openai import OpenAI

client = OpenAI(api_key="PUT-KEY-HERE")



def process_message(messages):
    
    try:
        print(f"[CHATGPT] Calling OpenAI with {len(messages)} messages...")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        # Extract the assistant's reply
        assistant_reply = response.choices[0].message.content
        print(f"[CHATGPT] Got response: {assistant_reply[:100]}...")

        # Append to message history
        messages.append({
            "role": "assistant",
            "content": assistant_reply
        })

        return messages

    except Exception as e:
        print(f"[CHATGPT] ERROR: {str(e)}")
        print(f"[CHATGPT] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        # Return original messages on error
        return messages
