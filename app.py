import os

import openai
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")


# @app.route("/", methods=("GET", "POST"))
def orginalIndex():
    if request.method == "POST":
        animal = request.form["animal"]
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(animal),
            temperature=0.6,
        )
        return redirect(url_for("index", result=response.choices[0].text))

    result = request.args.get("result")
    return render_template("index.html", result=result)

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        usertext = request.form["animal"]

        # msgs = [
        #     {"role": "system", "content": "You are a philosophy professor specializing in formal argumentation." },
        #     {"role": "user", "content": "Given the following argument, please identify the argument conclusion"
        #             " and the evidence supporting that conclusion. Put the conclusion and each item of evidence on a separate line."
        #             " Prefix the conclusion with 'conclusion:'.  Prefix each item of evidence with 'evidence; ' "},
        #     {"role": "user", "content": usertext},
        # ]

        msgs = [
            {"role": "system", "content": "You are a philosophy professor specializing in formal argumentation." },
            {"role": "user", "content": "Given the following argument, please identify the argument conclusion"
                                        ", the evidence supporting that conclusion.  Also identify any implicit assumptions made in the argument."
                                        " Format the response as a json object with a property for the conclusion, an array of evidence items, and an array of assumptions"},
            {"role": "user", "content": usertext},
        ]

        # msgs = [
        #     {"role": "system", "content": "You are a philosophy professor specializing in formal argumentation." },
        #     {"role": "user", "content": "Given the following argument, please identify the argument conclusion"
        #                                 ", the evidence supporting that conclusion.  Also identify any logical fallacies made in the argument."
        #                                 " Format the response as a json object with a property for the conclusion, an array of evidence items, and an array of fallacies."},
        #     {"role": "user", "content": usertext},
        # ]

        print(msgs)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=msgs,
            temperature=0.6,
        )
        print(response)
        print(response.choices[0].message.content)
        return redirect(url_for("index", result=response.choices[0].message.content))

    result = request.args.get("result")
    return render_template("index.html", result=result)

def generate_argument_prompt(animal):
    return """Given the following argument, please identify the argument conclusion and the evidence supporting that conclusion.
    Argument:""".format(animal)

def generate_prompt(animal):
    return """Suggest three names for an animal that is a superhero.

Animal: Cat
Names: Captain Sharpclaw, Agent Fluffball, The Incredible Feline
Animal: Dog
Names: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot
Animal: {}
Names:""".format(
        animal.capitalize()
    )
