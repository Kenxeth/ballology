const friendContainer = document.getElementById('friendsContainer');
const chatContainer = document.getElementById('chatContainer');
const messagesContainer = document.getElementById('messagesContainer');
let messageInput = document.getElementById('messageInput');

let currentFriend = null;

function openChatContainer(friend) {
  currentFriend = friend;
  messagesContainer.innerHTML = `
    <strong> <div>${friend}</div> <strong>
    <hr></hr>
  `;
  chatContainer.style.display = 'block';

}

function sendMessage(current_client, room_id) {
  const messageText = messageInput.value.trim();
  console.log("it was CLICKED.")
  if (messageText !== '') {
    const socket = io('http://localhost:5500')
    const messageElement = document.createElement('div');
    messageElement.textContent = `${current_client}:  ${messageText}`;
    messageElement.classList.add('message');

    socket.emit("save_message_to_db", {"user": current_client, "message": messageText, "room_id": room_id})
    messagesContainer.appendChild(messageElement);
    messageInput.value = '';
    messageInput.focus();
  }
}

// using a different function because if we use the same function that old messages
// would get re added into the db

function loadPreviousMessages(){
    const messageText = messageInput.value.trim();

    if (messageText !== '') {
        const messageElement = document.createElement('div');
        messageElement.textContent = `${messageText}`;
        messageElement.classList.add('message');

        messagesContainer.appendChild(messageElement);
        messageInput.value = '';
        messageInput.focus();
  }
}



function closeChat() {
  currentFriend = null;
  chatContainer.style.display = 'none';
}


window.addEventListener('load', function (event) {
    // if user clicks the enter button
    
   
    // fetching resources to validate the user + grab the users current friends
    fetch("http://127.0.0.1:5000/getCurrentFriends", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"data": "data"}) // filler data- need it for post req
        })
        .then((response) => response.json())
        .then((data) => {
            let friends = data["list_of_friends"] // list of current clients friends
            let current_client = data["current_client"] // current client username
           
           
            friends.forEach((friend) => {
                    const friendElement = document.createElement('div');
                    friendElement.classList.add('friend');
                    friendElement.textContent = friend;
                    friendElement.onclick = () => openChatContainer(friend);
                    friendContainer.appendChild(friendElement);
                    
                    // start a socket connection once a user clicks on a user to chat
                    friendElement.addEventListener("click", function () {

                        const socket = io('http://localhost:5500')
                        socket.once("connect", ()=>{
                            console.log("client connected")
                            socket.emit("request_message", {"data": {"jwt_token": data["jwt"],"userFriend": friend}})                        
                        })
                        

                        // UPDATING MESSAGE IN REAL TIME
                        socket.on("handle_new_message", (data)=>{
                            // if a user sent the message- then there is no reason why they should be handling the same message they already sent since its already there.
                        
                            console.log(data["user"],  current_client)
                            
                            if(data["user"] != current_client){
                                new_message = data["new_message"]
                                user = data["user"]
                                messageInput.value = `${user} : ${new_message}`
                                loadPreviousMessages()
                            }
                        })



                        let loaded_previous_messages = false
                        socket.on("send_room_messages", (data)=>{
                            // FIRST LOAD ALL THE PREVIOUS MESSAGES INTO THE CHAT
                            if (loaded_previous_messages == false){
                                let previous_room_messages = data["previous_room_messages"]
                                for (let i = 0; i < previous_room_messages.length; i++){
                                    let current_message = previous_room_messages[i]
                                    messageInput.value = `${current_message[0]} : ${current_message[1]}`
                                    loadPreviousMessages(current_client)
                                    loaded_previous_messages = true
                                }
                            }
                            
                            messageInput.addEventListener("keydown", (e) =>{
                                if (e.key ===  "Enter"){
                                    e.preventDefault()
                                    sendMessage(current_client, data["room_id"])
                                }
                            })

                        })
                        
                    })
                });
        })
        .catch((error) => console.error("Error:", error));
    });

