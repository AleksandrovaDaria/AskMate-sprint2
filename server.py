from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
)
import util
import datetime
import data_hendler
import csv
from config import *
from errors import *
from messages import *
from jinja2 import Environment

app = Flask(__name__)

@app.route("/")
@app.route("/")
@app.route("/list")
def question_list(messages_msg=None):
    user_id = util.get_user_id(request)
    with open(QUESTIONS_FILE, "r", newline="") as csvfile:
        questions = list(csv.DictReader(csvfile))
    order_by = request.args.get("order_by")
    order_direction = request.args.get("order_direction")
    if order_by != None:
        if order_direction == "desc":
            questions = sorted(
                questions,
                key=lambda i: int(i[order_by])
                if i[order_by].isnumeric()
                else i[order_by],
                reverse=True,
            )
        else:
            questions = sorted(
                questions,
                key=lambda i: int(i[order_by])
                if i[order_by].isnumeric()
                else i[order_by],
            )
    response = make_response(
        render_template("question_list.html", request=request, user_questions=questions, messages_msg=messages_msg, user_id=user_id)
    )
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/question/<question_id>/")
@app.route("/question/<question_id>/<string:messages_msg>")
def question_detail(question_id, messages_msg=None):
    user_id = util.get_user_id(request)
    with open(QUESTIONS_FILE, "r", newline="") as csvfile:
        questions = list(csv.DictReader(csvfile))
    question = next((q for q in questions if q["id"] == question_id), None)
    answers_to_question = data_hendler.read_specific_data(
        ANSWER_FILE, "question_id", question_id
    )
    response = make_response(
        render_template(
            "question_detail.html",
            question=question,
            answers=answers_to_question,
            messages_msg=messages_msg,
            user_id=user_id,
        )
    )
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/add-question", methods=["GET", "POST"])
def question():
    user_id = util.get_user_id(request)
    errors_msg = []
    if request.method == "POST":
        question_id = util.generate_id(QUESTIONS_FILE)
        submision_time = round(datetime.datetime.now().timestamp())
        views = 0
        vote = 0
        title = request.form.get("title")
        message = str(request.form.get("message"))
        imagename = ""
        if len(title) == 0:
            errors_msg.append(errors["empty_title"])
        if len(message) == 0:
            errors_msg.append(errors["empty_message"])
        if "image" in request.files:
            image = request.files["image"]
            if image.filename != "":
                if not util.is_allowed_file_extension(image.filename):
                    errors_msg.append(errors["wrong_file_extension"])
                else:
                    imagename = (
                        IMAGES_FOLDER
                        + str(question_id)
                        + "."
                        + util.get_file_extension(image.filename)
                    )
                    image.save(imagename)
        question = [
            question_id,
            submision_time,
            views,
            vote,
            title,
            message,
            imagename,
            user_id,
        ]
        if len(errors_msg) == 0:
            messages_msg = messages["added_question"]
            data_hendler.addtofile(question, QUESTIONS_FILE)
            return redirect(
                url_for(
                    "question_detail",
                    question_id=question_id,
                    messages_msg=messages_msg,
                )
            )
    response = make_response(
        render_template("add_question.html", form=request.form, errors_msg=errors_msg)
    )
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/question/<int:question_id>/new-answer", methods=["GET", "POST"])
def answer(question_id):
    user_id = util.get_user_id(request)
    errors_msg = []
    if request.method == "POST":
        id = util.generate_id(ANSWER_FILE)
        submission_time = round(datetime.datetime.now().timestamp())
        vote_number = 0
        message = str(request.form.get("message"))
        imagename = ""
        if len(message) == 0:
            errors_msg.append(errors["empty_message"])
        if "image" in request.files:
            image = request.files["image"]
            if image.filename != "":
                if not util.is_allowed_file_extension(image.filename):
                    errors_msg.append(errors["wrong_file_extension"])
                else:
                    imagename = (
                        IMAGES_FOLDER
                        + str(question_id)
                        + "-"
                        + str(id)
                        + "."
                        + util.get_file_extension(image.filename)
                    )
                    image.save(imagename)
        answer = [
            id,
            submission_time,
            vote_number,
            question_id,
            message,
            imagename,
            user_id,
        ]
        if len(errors_msg) == 0:
            messages_msg = messages["added_answer"]
            data_hendler.addtofile(answer, ANSWER_FILE)
            return redirect(
                url_for(
                    "question_detail",
                    question_id=question_id,
                    messages_msg=messages_msg,
                )
            )
    response = make_response(
        render_template(
            "add_answer.html",
            question_id=question_id,
            form=request.form,
            errors_msg=errors_msg,
        )
    )
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/question/<int:question_id>/delete/<int:answer_id>")
def delete_answer(question_id, answer_id):
    user_id = util.get_user_id(request)
    with open(ANSWER_FILE, "r", newline="") as csvfile:
        answers = list(csv.DictReader(csvfile))
    answer = next((a for a in answers if a["id"] == str(answer_id)), None)
    if user_id == answer["user_id"]:
        messages_msg = messages["delete_answer"]
        data_hendler.delete_data(ANSWER_FILE, answer_id, "id", ANSWER_HEADER)
    else:
        messages_msg = messages["cant_delete"]
    response = make_response(
        redirect(
            url_for(
                "question_detail",
                question_id=question_id,
                messages_msg=messages_msg,
            )
        )
    )
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/question/<int:question_id>/delete")
def delete_question(question_id):
    user_id = util.get_user_id(request)
    with open(QUESTIONS_FILE, "r", newline="") as csvfile:
        questions = list(csv.DictReader(csvfile))
    question = next((q for q in questions if q["id"] == str(question_id)), None)
    if user_id == question["user_id"]:
        messages_msg = messages["delete_question"]
        data_hendler.delete_data(QUESTIONS_FILE, question_id, "id", QUESTION_HEADER)

        with open(ANSWER_FILE, "r", newline="") as csvfile:
            answers = list(csv.DictReader(csvfile))
        for a in answers:
            if a["question_id"] == str(question_id):
                messages_msg = messages["delete_answer"]
                data_hendler.delete_data(
                    ANSWER_FILE, question_id, "question_id", ANSWER_HEADER
                )
    else:
        messages_msg = messages["cant_delete"]
    response = make_response(
        redirect(
            url_for("question_list", question_id=question_id, messages_msg=messages_msg)
        )
    )
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/question/<int:question_id>/vote")
def vote_question(question_id):
    messages_msg = ""
    user_id = util.get_user_id(request)
    with open(QUESTIONS_FILE, "r", newline="") as csvfile:
        questions = list(csv.DictReader(csvfile))
    question = next((q for q in questions if q["id"] == str(question_id)), None)
    response = make_response(
        redirect(
            url_for("question_list", messages_msg=messages_msg)
        )
    )
    if user_id != question["user_id"]:
        messages_msg = messages["vote_added"]
        data_hendler.add_vote(QUESTIONS_FILE, question_id, "id", QUESTION_HEADER)
        response.set_cookie("vote_question_"+str(question_id), "1")
    else:
        messages_msg = messages["cant_vote"]
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.route("/question/<int:question_id>/vote/<int:answer_id>")
def vote_answer(question_id, answer_id):
    messages_msg = ""
    user_id = util.get_user_id(request)
    with open(ANSWER_FILE, "r", newline="") as csvfile:
        answers = list(csv.DictReader(csvfile))
    answer = next((a for a in answers if a["id"] == str(answer_id)), None)
    response = make_response(
        redirect(
            url_for("question_detail", question_id=question_id,  messages_msg=messages_msg)
        )
    )
    if user_id != answer["user_id"]:
        messages_msg = messages["vote_added"]
        data_hendler.add_vote(ANSWER_FILE, answer_id, "id", ANSWER_HEADER)
        response.set_cookie("vote_answer_"+str(question_id)+"-"+str(answer_id), "1")
    else:
        messages_msg = messages["cant_vote"]
    if not request.cookies.get("userID"):
        response.set_cookie("user_id", user_id)
    return response


@app.template_filter("post_time")
def show_post_date(timestamp):
    return util.translate_timestamp(timestamp)


@app.route("/question/<question_id>/edit", methods=["GET", "POST"])
def question_edit(question_id):
    user_id = util.get_user_id(request)
    errors_msg = []
    if request.method == "POST":
        with open(QUESTIONS_FILE, "r", newline="") as csvfile:
            questions = list(csv.DictReader(csvfile))
        question = next((q for q in questions if q["id"] == question_id), None)
        if question:
            title = request.form.get("title")
            message = str(request.form.get("message"))
            imagename = question["image"]
            if len(title) == 0:
                errors_msg.append(errors["empty_title"])
            if len(message) == 0:
                errors_msg.append(errors["empty_message"])
            if "image" in request.files:
                image = request.files["image"]
                if image.filename != "":
                    if not util.is_allowed_file_extension(image.filename):
                        errors_msg.append(errors["wrong_file_extension"])
                    else:
                        imagename = (
                            IMAGES_FOLDER
                            + str(question_id)
                            + "."
                            + util.get_file_extension(image.filename)
                        )
                        image.save(imagename)

            if len(errors_msg) == 0:
                question["title"] = title
                question["message"] = message
                question["image"] = imagename

                with open(QUESTIONS_FILE, "w", newline="") as csvfile:
                    fieldnames = [
                        "id",
                        "submission_time",
                        "view_number",
                        "vote_number",
                        "title",
                        "message",
                        "image",
                        "user_id",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(questions)

                messages_msg = messages["edited_question"]
                return redirect(
                    url_for(
                        "question_detail",
                        question_id=question_id,
                        messages_msg=messages_msg,
                    )
                )

    with open(QUESTIONS_FILE, "r", newline="") as csvfile:
        questions = list(csv.DictReader(csvfile))
    question = next((q for q in questions if q["id"] == question_id), None)
    if question:
        response = make_response(
            render_template(
                "question_edit.html",
                question=question,
                form=request.form,
                errors_msg=errors_msg,
            )
        )
        if not request.cookies.get("userID"):
            response.set_cookie("user_id", user_id)
        return response
    else:
        return redirect(url_for("question_list"))


if __name__ == "__main__":
    app.run()
