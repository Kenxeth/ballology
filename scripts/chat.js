const socket = io()
// receives handshake and initiates a websocket connection with server
socket.on("connect", ()=>{
    console.log("CLIENT CONNECTED");
})
