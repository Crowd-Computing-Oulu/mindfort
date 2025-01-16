from openai import OpenAI

client = OpenAI(api_key="PUT-KEY-HERE")



def process_message(messages):
    
    print(messages)
    try:
        # Call OpenAI or any other model API to generate the assistant's reply
        response = client.chat.completions.create(model="gpt-4o",  # Specify the desired model
        messages=messages)

        # Extract the assistant's reply from the response
        assistant_reply = response.choices[0].message.content

        # Append the assistant's reply to the message history
        messages.append({
            "role": "assistant",
            "content": assistant_reply
        })
    
        return messages

    except Exception as e:
        print(f"Error while processing message: {e}")
        return messages
