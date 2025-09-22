const URL_API = "http://localhost:8000/"

document.addEventListener("DOMContentLoaded", () => {
    let createQuestionButton = document.getElementById("btn-create-question")
    createQuestionButton.addEventListener("click", () => createQuestion())
})

const createQuestion = async () => {
    let today = new Date()
    axios.post(URL_API + "question/create", {
        question: "Quelle est la capitale de la France ?",
        subject: "Géographie",
        use: "quiz",
        correct: ["Paris"],
        responses: [
            { "id": "1", "text": "Paris" },
            { "id": "2", "text": "Londres" },
            { "id": "3", "text": "Berlin" },
            { "id": "4", "text": "Madrid" }
        ],
        remark: "Question basique de culture générale",
        metadata: {
            author: "Admin",
            difficulty: "facile"
        },
        date_creation: today.toISOString(),
        date_modification: null
    })
    .then(function (response) {
        console.log(response.data)
    })
    .catch(function (error) {
        console.error(error)
    })
}