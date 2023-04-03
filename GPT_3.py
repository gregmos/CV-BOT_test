import openai

def improve_description(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Imagine that you are a career consultant and you are given a text describing a professional, and you need to improve it."},
            {"role": "user", "content": f"Transform and rephrase my professional description about me into a more professional and appealing version. Try not to use a lot of 'I's', and remember that you are writing in the first person: {text} Provide only the improved text in your reply."},
        ],
        max_tokens=1000,
    )

    assistant_message = response.choices[0].message['content']
    return assistant_message.strip()

def improve_job_duties(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Imagine that you are a career consultant and you are given a text of job duties, and you need to improve it."},
            {"role": "user", "content": f"Transform and rephrase the following description of job duties into a more professional and appealing version, with dashes as bullet points : {text} Provide only the improved text in your reply."},
        ],
        max_tokens=1000,
    )

    assistant_message = response.choices[0].message['content']
    return assistant_message.strip()

def improve_achievements(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Imagine that you are a career consultant and you are given a text of job duties, and you need to improve it."},
            {"role": "user", "content": f"Transform and rephrase the following job achievements into a more professional and appealing version, with dashes as bullet points: {text} Provide only the improved text in your reply."},
        ],
        max_tokens=1000,
    )

    assistant_message = response.choices[0].message['content']
    return assistant_message.strip()