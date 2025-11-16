const API_BASE_URL = "http://127.0.0.1:5000";

// --- AUTH HELPERS ---
function getToken() { return localStorage.getItem('auth_token'); }
function getUsername() { return localStorage.getItem('user_id'); }
function logout() { localStorage.clear(); window.location.href = "/templates/index.html"; }

// --- LOGIN ---
async function handleLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = "Verifying...";
    
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const res = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem("auth_token", data.auth_token);
            localStorage.setItem("user_id", data.username);
            window.location.href = "home.html";
        } else {
            alert(data.message);
        }
    } catch (err) { alert("Server error. Is app.py running?"); }
    btn.innerText = originalText;
}

// --- SIGNUP ---
async function handleSignup(e) {
    e.preventDefault();
    const username = document.getElementById("newUsername").value;
    const password = document.getElementById("newPassword").value;

    try {
        const res = await fetch(`${API_BASE_URL}/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.setItem("auth_token", data.auth_token);
            localStorage.setItem("user_id", data.username);
            window.location.href = "home.html";
        } else { alert(data.message); }
    } catch (err) { console.error(err); }
}

// --- ROADMAP GENERATION ---
async function generateRoadmap(e) {
    e.preventDefault();
    const token = getToken();
    if (!token) return window.location.href = "index.html";

    const btn = document.getElementById("generate-btn");
    const display = document.getElementById("goals-display");
    
    btn.disabled = true;
    btn.innerText = "AI is thinking...";
    display.innerHTML = "<p style='text-align:center; margin-top:20px;'>✨ Constructing your path to success...</p>";

    const careerGoal = document.getElementById("careerGoal").value;
    const yearlyGoal = document.getElementById("yearlyGoal").value;

    try {
        const res = await fetch(`${API_BASE_URL}/generate_plan`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ career_goal: careerGoal, yearly_goal: yearlyGoal })
        });
        const data = await res.json();

        if (res.ok) {
            renderPlan(data.plan);
        } else {
            display.innerHTML = `<p style="color:#ff6b6b">Error: ${data.message}</p>`;
        }
    } catch (err) {
        display.innerHTML = `<p style="color:#ff6b6b">Connection Failed.</p>`;
    } finally {
        btn.disabled = false;
        btn.innerText = "Regenerate Plan";
    }
}

// --- RENDER PLAN (FANCY CARDS) ---
function renderPlan(plan) {
    const display = document.getElementById("goals-display");
    let html = "";
    
    // Loop through keys 1 to 12
    for (let i = 1; i <= 12; i++) {
        const month = plan[String(i)];
        if (month) {
            html += `
                <div class="month-card">
                    <div class="month-header">Month ${i}</div>
                    <div class="month-goal">${month.monthly_goal}</div>
                    <ul class="task-list">
                        ${month.weekly.map(task => `<li>${task}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    }
    display.innerHTML = html;
}

// --- CHAT FUNCTIONALITY ---
async function sendChat() {
    const input = document.getElementById("chatInput");
    const messages = document.getElementById("messages");
    const text = input.value.trim();
    
    if (!text) return;

    // User Msg
    messages.innerHTML += `<div class="msg user">${text}</div>`;
    input.value = "";
    messages.scrollTop = messages.scrollHeight;

    // Bot Loading
    const loadingId = "loading-" + Date.now();
    messages.innerHTML += `<div id="${loadingId}" class="msg bot">...</div>`;

    try {
        const res = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        
        document.getElementById(loadingId).remove();
        messages.innerHTML += `<div class="msg bot">${data.bot_message}</div>`;
        messages.scrollTop = messages.scrollHeight;

    } catch (err) {
        document.getElementById(loadingId).innerText = "Error connecting.";
    }
}

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    // Check what page we are on
    if (document.getElementById("loginForm")) {
        document.getElementById("loginForm").addEventListener("submit", handleLogin);
    }
    if (document.getElementById("signupForm")) {
        document.getElementById("signupForm").addEventListener("submit", handleSignup);
    }
    if (document.getElementById("roadmap-form")) {
        document.getElementById("user-id-display").innerText = getUsername() || "Guest";
        document.getElementById("roadmap-form").addEventListener("submit", generateRoadmap);
        
        // Try to load existing plan
        // (Optional: You can implement fetchPlan on load like in previous versions)
    }
    if (document.getElementById("welcomeUser")) {
        document.getElementById("welcomeUser").innerText = getUsername() || "User";
    }
});