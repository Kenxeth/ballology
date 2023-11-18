
window.addEventListener('load', function () {
    const chatBtn = document.getElementById('chatBtn');
    const chatContainer = document.getElementById('chatContainer');

    // Toggle chat container visibility
    chatBtn.addEventListener('click', function () {
        if (chatContainer.style.display == "block"){
            chatContainer.style.display = "none"
            chatBtn.innerHTML = "Open Chat"
        }else{
            chatContainer.style.display = "block"
            chatBtn.innerHTML = "Close Chat"
        }
    });

    // Populate chat rooms dynamically (you can fetch this data from a server)
    const chatList = document.getElementById('chatList');

    // collect all current friends and put it in a friendsDict
   
    fetch("http://127.0.0.1:5000/getCurrentFriends", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"data": "data"})
        })
        .then((response) => response.json())
        .then((data) => {
            let friendsList = data["list_of_friends"]
            friendsList.forEach(friend => {
                // honestly its not printing figure out whats wrong
                console.log(friend)
                const chatBox = document.createElement('div');
                chatBox.className = 'chatRoom';
                chatBox.style.marginBottom = "25px"
                chatBox.textContent = friend;
                chatList.appendChild(chatBox);
                
                chatBox.addEventListener("click", function () {
                    const socket = io('http://localhost:5500')
        
                    socket.on("connect", ()=>{
                        console.log("client connected")
                        socket.emit("request_message", {"data": {"jwt_token": data["jwt_token"],"userFriend": chatBox.textContent}})
                    
                        socket.on("send_room_messages", (data)=>{
                            console.log("data: ", data)
                        })
                    })
                })
            });
        })
        .catch((error) => console.error("Error:", error));
});