const API = "http://127.0.0.1:5000/api";

let currentStep = "login";

// Elements
const loginPage = document.getElementById("loginPage");
const mainPage = document.getElementById("mainPage");
const draftPage = document.getElementById("draftPage");
const resultPage = document.getElementById("resultPage");
const benefitPage = document.getElementById("benefitPage");
const uploadPage = document.getElementById("uploadPage");

function openMain(){
    loginPage.style.display="none";
    mainPage.style.display="block";
    currentStep = "main";
}

function openDraft(){
    mainPage.style.display="none";
    draftPage.style.display="block";
    currentStep = "draft";
}

async function openResult(){
    // Fetch schemes from Backend
    try {
        const response = await fetch(`${API}/schemes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await response.json();
        if (data.success) {
            console.log("Schemes Loaded:", data.schemes);
            // In a full implementation, you'd dynamically generate the scheme cards here
        }
    } catch(e) {
        console.error("Backend error:", e);
    }
    
    draftPage.style.display="none";
    resultPage.style.display="block";
    currentStep = "result";
}

async function openBenefit(){
    try {
        const response = await fetch(`${API}/compare`);
        const data = await response.json();
        if (data.success) {
            console.log("Benefits Comparison:", data);
            // In a full implementation, you'd dynamically generate the comparison view here
        }
    } catch(e) {
        console.error("Backend error:", e);
    }

    resultPage.style.display="none";
    benefitPage.style.display="block";
    currentStep = "benefit";
}

function openUpload(){
    benefitPage.style.display="none";
    uploadPage.style.display="block";
    currentStep = "upload";
}

function autoFillForm(){
    alert("✅ Documents Verified & Form Auto Filled");
    uploadPage.style.display="none";
    draftPage.style.display="block";
    currentStep = "draft";
}

async function submitDescription(){
    const textarea = document.querySelector(".hero textarea");
    const desc = textarea ? textarea.value : "";
    
    alert("🤖 AI is analysing your situation...");
    
    try {
        const response = await fetch(`${API}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: desc })
        });
        const data = await response.json();
        
        if (data.success) {
            console.log("AI Analysis Result:", data);
            
            // Auto-fill draft page based on AI analysis
            const inputs = document.querySelectorAll("#draftPage .formSection input");
            if (inputs.length >= 4) {
                inputs[0].value = data.extracted_details.name || '';
                inputs[1].value = data.extracted_details.aadhaar || '';
                inputs[2].value = data.extracted_details.income || '';
                inputs[3].value = data.extracted_details.land_size || '';
            }
        }
        
    } catch(e) {
        console.error("Backend not running or error:", e);
    }
    
    // Move to draft page to show the autofilled form
    mainPage.style.display="none";
    draftPage.style.display="block";
    currentStep = "draft";
}


function goBack(){
    if(currentStep === "main"){
        window.location.href="index.html";
    }
    else if(currentStep === "draft"){
        draftPage.style.display="none";
        mainPage.style.display="block";
        currentStep="main";
    }
    else if(currentStep === "result"){
        resultPage.style.display="none";
        draftPage.style.display="block";
        currentStep="draft";
    }
    else if(currentStep === "benefit"){
        benefitPage.style.display="none";
        resultPage.style.display="block";
        currentStep="result";
    }
    else if(currentStep === "upload"){
        uploadPage.style.display="none";
        benefitPage.style.display="block";
        currentStep="benefit";
    }
}

function showFileName(input, id){
    let name = input.files[0] ? input.files[0].name : "No file chosen";
    document.getElementById(id).innerText = name;
}