const url = "http://localhost:8000/"

let randomNumberButton;

const requestNumber = async () => {
    try {
        let randomNumber = document.getElementById("random-number")

        randomNumberButton.classList.add("is-loading")

        const response = await fetch(url + "random")

        if (!response.ok) {
            randomNumberButton.classList.remove("is-loading")
            throw new Error(`Response status: ${response.status}`)
        }
        const result = await response.json()
        randomNumberButton.classList.remove("is-loading")
        randomNumber.innerText = result["random_number"]
    } catch (error) {
        randomNumberButton.classList.remove("is-loading")
        console.error(error.message)
    }
}

document.addEventListener("DOMContentLoaded", () => {
    randomNumberButton = document.getElementById("btn-random-number")
    randomNumberButton.addEventListener("click", () => requestNumber())
})