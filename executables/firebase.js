    import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
    import { getStorage }      from "https://www.gstatic.com/firebasejs/9.22.2/firebase-storage.js";
    import { getAuth, signInAnonymously } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";
    const firebaseConfig = {
      apiKey: "AIzaSyB6kuGJdqzZvorG6zb5slCASpSUMnoX0Zg",
      authDomain: "cpsc455techcloud.firebaseapp.com",
      projectId: "cpsc455techcloud",
      storageBucket: "cpsc455techcloud.firebasestorage.app",
      messagingSenderId: "733104077877",
      appId: "1:733104077877:web:d34e457e57e7eb10bb057c",
      measurementId: "G-QLRT3M6T0X"
      };
    const app     = initializeApp(firebaseConfig);
    const auth    = getAuth(app);
    window.storage = getStorage(app);
    signInAnonymously(auth)