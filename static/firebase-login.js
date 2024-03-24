'use strict';

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";


const firebaseConfig = {
    apiKey: "AIzaSyCtapNnemM3053aR11H6vjtAddOwJoxHDk",
    authDomain: "ev-bl-418017.firebaseapp.com",
    projectId: "ev-bl-418017",
    storageBucket: "ev-bl-418017.appspot.com",
    messagingSenderId: "781390441846",
    appId: "1:781390441846:web:8ea83717c9e18eee715e57"
};

window.addEventListener("load", function () {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    updateUI();

    document.getElementById("login").addEventListener('click', function () {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        signInWithEmailAndPassword(auth, email, password)
            .then(() => {
                console.log("User logged in successfully!");
            })
            .catch((error) => {
                console.log(error.code, error.message);
            });
    });

    document.getElementById("sign-out").addEventListener('click', function () {
        signOut(auth)
            .then(() => {
                console.log("User signed out successfully!");
            })
            .catch((error) => {
                console.error("Error signing out:", error);
            });
    });

    onAuthStateChanged(auth, (user) => {
        updateUI(user);
    });

    function updateUI(user) {
        const loginBox = document.getElementById("login-box");
        const signOutButton = document.getElementById("sign-out");
        const links = document.querySelectorAll("a");

        if (user) {
            // User is signed in
            loginBox.style.display = "none"; 
            signOutButton.style.display = "block"; 

            // Show links
            links.forEach(link => {
                link.style.display = "block";
            });
        } else {
            // User is signed out
            loginBox.style.display = "block"; 
            signOutButton.style.display = "none"; 

            // Hide links
            links.forEach(link => {
                link.style.display = "none";
            });
        }
    }
});