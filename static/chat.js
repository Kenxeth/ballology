const socket = io()
// receives handshake and initiates a websocket connection with server
socket.on("connect", ()=>{
    console.log("CLIENT CONNECTED");
})

// js has no support for getting a cookie so you have to make your own function
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

const inputText = document.getElementById('inputText');
const submitButton = document.getElementById('submitButton');
const output = document.getElementById('output');

submitButton.addEventListener('click', function() {
    let username = getCookie("username")

    const inputValue = {[username] : inputText.value};
    console.log(inputValue)
    // Create a new paragraph element to display the input value
    const newParagraph = document.createElement('p');
    listofKeys = Object.keys(inputValue)
    key = listofKeys[0]
    newParagraph.textContent = key + ":     " + inputValue[username];

    // Insert the new paragraph at the top of the output div
    output.insertBefore(newParagraph, output.firstChild);
    
    socket.emit("message", inputValue)

    inputText.value = '';
});