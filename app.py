import json
import os

import openai
from werkzeug.exceptions import HTTPException

from flask import Flask, redirect, render_template, request, url_for, jsonify



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


@app.route("/article", methods=("GET", "POST"))
def article_index():
    if request.method == "POST":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "what is the article we are discussing?"},
                {"role": "assistant", "content": article},
                {"role": "user", "content": "Please outline all arguments made in the article."}
            ]
        )
        text_result = '\n'.join([c['message']['content'] for c in response.choices])
        return redirect(url_for("article_index", result=text_result))

    result = request.args.get("result")
    if result is not None:
        result = result.split('\n')
    return render_template("article_index.html", result=result)


def trim_str (input: str) -> str:
    ignored_characters = set(['\'', '"', ' ', '\t', '\n'])
    while input[0] in ignored_characters:
        input = input[1:]
    while input[-1] in ignored_characters:
        input = input[:-1]
    return input

standard_request = '''
Please outline all arguments made in the article.
Format the response as a JSON array of JSON objects, with the argument listed under the "argument" property.
In each object, please also include the following properties:
   quotes - a list of all the quotes from the article that support the given argument
   assumptions - a list of assumptions (both explicit and implicit) assumed by the given argument
   fallacies - a list of logical fallacies that the argument might exhibit
   rating - the probability that the argument is true
'''

@app.route('/article_json', methods=['POST'])
def article_json():
    input_json = request.get_json(force=True)
    if 'content' not in input_json:
        raise HTTPException('content required')
    content = input_json['content']
    if isinstance(content, list):
        content = '\n'.join(content)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "what is the article we are discussing?"},
            {"role": "assistant", "content": content},
            {"role": "user", "content": standard_request}
        ]
    )
    text_result = [c['message']['content'] for c in response.choices]
    json_result = [json.loads(t) for t in text_result]
    for jr in json_result:
        for r in jr:
            # go through quotes, see if they are there, and get offsets
            for i, q in enumerate(r['quotes']):
                q = trim_str(q)
                q_json = { 'quote': q }
                q_parts = q.split('...')
                if len(q_parts) > 1:
                    starts = [content.lower().find(qq.lower()) for qq in q_parts]
                    if min(starts) < 0:
                        q_json['found'] = False
                    else:
                        q_json['found'] = True
                        q_json['start'] = min(starts)
                        q_json['end'] = max([starts[i] + len(q_parts[i]) for i in range(len(q_parts))])
                else:
                    start = content.lower().find(q.lower())
                    if start == -1:
                        q_json['found'] = False
                    else:
                        q_json['found'] = True
                        q_json['start'] = start
                        q_json['end'] = start + len(q)
                r['quotes'][i] = q_json

    return jsonify(json_result)

    # text_result = [{'text': t} for t in '\n'.join([c['message']['content'] for c in response.choices]).split('\n')]
    # for i in range(len(text_result)):
    #     print(f'Checking response {text_result[i]}')
    #     messages = [
    #         {"role": "system", "content": "what is the article we are discussing?"},
    #         {"role": "assistant", "content": content},
    #         {"role": "system", "content": "what argument are we discussing?"},
    #         {"role": "assistant", "content": text_result[i]['text']},
    #         {"role": "user", "content": "Where in the article is this argument discussed? Please answer in the form of a list of quotes, separated by a pipe (\"|\") character."}
    #     ]
    #     response = openai.ChatCompletion.create(
    #         model="gpt-3.5-turbo",
    #         messages=messages
    #     )
    #     text_bounds = '|'.join([c['message']['content'] for c in response.choices]).split('|')
        
    #     text_result[i]['result'] = text_bounds

    # return jsonify({'results': text_result})



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


article = '''
Nearly five years ago, Pittsburgh and the nation were traumatized when a gunman entered the Tree of Life synagogue building and killed 11 worshipers attending Shabbat morning services. This attack on the Jewish community — seemingly motivated by white supremacy and antisemitic hatred — left us all enraged and heartbroken. All Americans deserve to gather with their communities and practice their faiths in safety. The horrific violence at Tree of Life was an affront to that ideal.

The victims, their families and the community deserve justice. The gunman, Robert G. Bowers, was ready to plead guilty and accept life in prison, but the Justice Department rejected that offer and moved forward with a capital murder trial. Bowers has now been found guilty, and the jury is hearing arguments over whether to impose the death penalty. But the government’s decision to pursue the death penalty, itself a product and perpetuation of white supremacy, cannot be the answer that brings healing and closure — or justice.

The death penalty is a morally bankrupt and inescapably racist institution. The horrific acts the defendant was found guilty of do not change this reality. Nor does the fact that Bowers is a White man charged with acting out of racial and antisemitic hatred eradicate the racism and inequality entrenched in the death penalty. Indeed, the prosecution’s pursuit of death in this case has resulted in racial exclusion that harms the entire Pittsburgh community.

A jury is supposed to represent the conscience of the community, but to win a verdict of death, lawyers from the Justice Department — including the Civil Rights Division, which is responsible for enforcing federal statutes prohibiting discrimination — participated in a selection process that excluded all Black and Latino people from the jury. Striking these members of the community was part and parcel of the DOJ’s strategy to pick the jurors it deemed most avid to choose capital punishment.

The court sent 1,500 questionnaires to prospective jurors, and more than 200 appeared for questioning. These jurors were asked about hardship, their knowledge of the case and their potential bias and were subjected to a process known as death qualification. Sixty-eight made it past the interviews; only four were Black, and one was Latino. The government then struck all five of these jurors. The final jury, including alternates, consists of 17 White people and one Asian person.

Death qualification is the first legal mechanism facilitating this exclusion of Black and Latino jurors. It requires that to be eligible to serve, jurors must declare they are not opposed to capital punishment. Death-qualified jurors must also be willing to vote to impose death if they find it to be the appropriate sentence. Decades of evidence shows that death qualification results in the disproportionate exclusion of groups that are more likely to oppose capital punishment, including Black people and other people of color as well as followers of certain religions. Death qualification also results in juries that are more likely to convict and more likely to reach hasty decisions.

The second legal mechanism at play is the peremptory strike, which allows prosecutors to exclude otherwise eligible jurors — unless the defense can prove that the strikes were motivated by intentional racism or gender discrimination, an extremely difficult standard to meet. Prosecutors in this case used their discretionary strikes to remove the remaining Black and Latino jurors.

Historical and current experiences of racial discrimination contribute to the distrust that many Black people and other people of color feel toward the death penalty, which in turn leads to systemic juror disqualification in capital cases. Our modern death penalty is an outgrowth of lynching and racial terror, with state-approved capital punishment gradually replacing racialized mob justice. And just like lynching, the death penalty today disproportionately kills Black people. Though Black Americans make up only about 13 percent of the population, they represent 34 percent of all executions between 1976 and 2022 and 41 percent of the current death row population. These facts contribute to the Black community’s distrust of and disdain for this extreme punishment. And even though this is a case without a Black defendant or a Black victim, Black voices in the Pittsburgh area remain part of the conscience of the community.

With its selection of a nearly all-White jury, the Justice Department is stating that preserving its ability to win a death sentence justifies excluding Black and Latino jurors from one of the most vital instruments of our democracy. We should say no to this.

The death penalty diminishes us all every time it transforms a legal proceeding into a parade of horrors played out in front of jurors whose most important qualification is their willingness to vote to kill. President Biden appeared to recognize this while campaigning on a still unfulfilled promise to end the federal death penalty. It’s not too late to make good on this commitment and halt the cycle of discrimination at the core of capital punishment. The first step: Disband this nonrepresentative jury and stop pursuing the death penalty in Pittsburgh.'''
def generate_reasoning_prompt():
    return f'''Please outline the arguments made in the following article:

    {article}
    '''
