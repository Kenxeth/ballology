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

// this function serves a purpose of loading the messages as soon as the client 
// opens up the browser
async function show_messages(){
    const response = await fetch("http://127.0.0.1:5000/getChatMessages");
    const chatMessages = await response.json();
    // chatMessages is a list of all the chatMessages that we get from our API endpoint
    // we are getting each message and displaying it on the page
    for(const message of chatMessages){
        const newParagraph = document.createElement('p');
        newParagraph.textContent = message[0] + ":  " + message[1]
        output.insertBefore(newParagraph, output.firstChild);
    }
}

show_messages()

submitButton.addEventListener('click', function() {
    // get username from cookie
    let username = getCookie("username")
    // sending back a dict with username: message to the server 
    const inputValue = {[username] : inputText.value};
    
    listofKeys = Object.keys(inputValue)
    key = listofKeys[0]
    const newParagraph = document.createElement('p');
    newParagraph.textContent = key + ":     " + inputValue[username];

    // Insert the new paragraph at the top of the output div
    output.insertBefore(newParagraph, output.firstChild);
    
    socket.emit("message", inputValue)

    inputText.value = '';
});