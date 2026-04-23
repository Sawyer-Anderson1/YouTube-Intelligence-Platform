import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDJegUab2MjSxG9v1unMe9wGjyCw1A82l4",
  authDomain: "intelligence-platform-8c906.firebaseapp.com",
  projectId: "intelligence-platform-8c906",
  storageBucket: "intelligence-platform-8c906.firebasestorage.app",
  messagingSenderId: "334409426540",
  appId: "1:334409426540:web:e26efae0e0d4fdb25a1a49",
  measurementId: "G-KQX6XB0QSX"
};


const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider };
