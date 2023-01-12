import openai


open_ai_org = ""
open_ai_key = ""

with open("config_local.json", "r") as f:
    generation_params = json.load(f)
open_ai_key = generation_params.get("open_ai_key", "")
open_ai_org = generation_params.get("open_ai_org", "")

openai.api_key = open_ai_key

# prompt = "Question: What is the goal of SpaceX? Answer: "

prompt = "Task: You are a chatbot that helps the user order food. You know only information stored in the list of FAQ below. You MUST NOT provide any information unless in is in the list of FAQ. You MUST NOT mention any entity if it is not in your list of FAQ. \n\nThe list of FAQ:\nQuestion: What kinds of pizza do you have?\nAnswer: We have Margarita, Pepperoni, meatball pizza and pineapple pizza. \n\nQuestion: What kinds of food do you offer?\nAnswer: We sell Italian food, so we have pizza, pasta, risotto and some Italian desserts.\n\nQuestion: What drinks do you offer?\nAnswer: We only serve non-alcoholic drinks. We have different fizzy drinks, juices, tea, and coffee. As for coffee, the kinds are Espresso, Americano, Capucchino, and Latte.\n\nQuestion: Can I book a table?\nAnswer: Unfortunately, we do not book tables. \n\nQuestion: Is your food expensive?\nAnswer: We try to make our food as affordable as possible. The average bill for one-person dinner is around 20$, including salad, the main course, and the dessert. \n\nDialog example:\nHuman: What food do you serve?\nAI: We sell Italian food, such as pizza, pasta, risotto and some Italian desserts. \n\n A user enters the chat. Answer their questions."


response = openai.Completion.create(
  model="text-davinci-003",
  prompt=prompt,
  temperature=0.8,
  max_tokens=200,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

if "choices" in response:
        if len(response["choices"]):
            if "text" in response["choices"][0]:
                result = response["choices"][0]["text"]
                print(response["choices"][0]["text"])
