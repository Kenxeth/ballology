// generally what the user can change in their profile: image, description.
let userProfileImage = document.getElementById("userProfileImage")
let userProfileDescription = document.getElementById("userProfileDescription")
// once this button is clicked, all input boxes and buttons should be avaliable
// so that the user can change what they want
let changeUserProfileButton = document.getElementById("changeUserProfileButton")
// input boxes where the user can type the changes they want to submit
let changeUserProfileImageInput = document.getElementById("changeUserProfileImage")
let changeUserProfileDescInput = document.getElementById("changeUserProfileDesc")

//  buttons that are currently invisible- they are meant to grab the users profile changes
// from the inbox boxes above
let submitUserProfileImageChangesBtn = document.getElementById("submitUserProfileImageChanges")
let submitUserProfileDescChangesBtn = document.getElementById("submitUserProfileDescChanges")

// when user clicks change user profile button, user should see some things pop up
changeUserProfileButton.addEventListener("click", ()=>{
    // make the buttons and inputs visible
    submitUserProfileDescChangesBtn.style.display = "block"
    submitUserProfileImageChangesBtn.style.display = "block"
    changeUserProfileDescInput.setAttribute("type", "text")
})
// the user can input the changes they want and once they click submit
// grab the value of the input box and send it along to the server

