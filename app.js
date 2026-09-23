const $ = id => document.getElementById(id);
function show(id){$(id).style.display='grid'}
function hide(id){$(id).style.display='none'}

async function addTask(){
  const r=await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:$('title').value,subject:$('subject').value,due_date:$('due').value})});
  const d=await r.json();
  if(d.error){alert(d.error);return}
  hide('taskModal'); location.reload();
}
async function toggleTask(id){
  await fetch('/api/tasks/'+id,{method:'PATCH'}); location.reload();
}
async function deleteTask(id){
  if(!confirm('Delete this assignment?')) return;
  await fetch('/api/tasks/'+id,{method:'DELETE'}); location.reload();
}
async function summarize(){
  $('summary').innerHTML='Working...';
  const r=await fetch('/api/summarize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('notice').value})});
  const d=await r.json();
  if(d.error){$('summary').innerHTML=d.error;return}
  $('summary').innerHTML='<b>Summary</b><br>'+escapeHtml(d.short)+'<br><br><b>Keywords:</b> '+escapeHtml(d.keywords.join(', ')||'None detected');
}
async function makePlan(){
  $('plan').innerHTML='Creating...';
  const r=await fetch('/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subjects:$('subjects').value,days:$('days').value,hours:$('hours').value})});
  const d=await r.json();
  if(d.error){$('plan').innerHTML=d.error;return}
  $('plan').innerHTML=d.days.map(x=>'<b>Day '+x.day+'</b><br>• '+x.items.join('<br>• ')).join('<hr>');
}
async function chatSend(){
  const msg=$('message').value.trim(); if(!msg)return;
  $('chat').innerHTML+='<div class="user">'+escapeHtml(msg)+'</div>';
  $('message').value='';
  const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
  const d=await r.json();
  $('chat').innerHTML+='<div class="bot">'+escapeHtml(d.reply)+'</div>';
  $('chat').scrollTop=$('chat').scrollHeight;
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}
async function loadLectures() {
    const response = await fetch("/api/lectures");
    const lectures = await response.json();

    const list = document.getElementById("lectureList");

    if (!lectures.length) {
        list.innerHTML = `
            <p class="empty-state">
                No missed classes added yet.
            </p>
        `;
        return;
    }

    list.innerHTML = lectures.map(lecture => `
        <div class="lecture-card">
    <h3>🎓 ${lecture.title}</h3>
    <p><strong>Subject:</strong> ${lecture.subject}</p>
    <p><strong>Date:</strong> ${lecture.lecture_date}</p>

    ${
        lecture.notes
        ? `<p><strong>Notes:</strong> ${lecture.notes}</p>`
        : ""
    }

    ${
        lecture.video_url
        ? `<a href="${lecture.video_url}" target="_blank">
            ▶️ Watch Lecture
           </a>`
        : ""
    }

    <br><br>

    <button onclick="deleteLecture(${lecture.id})">
        🗑️ Delete
    </button>
    <br><br>

<button onclick="generateNotes(${lecture.id})">
    📄 Generate AI Notes
</button>

<button onclick="generateQuiz(${lecture.id})">
    🧠 Generate AI Quiz
</button>

<div id="notes-${lecture.id}" class="ai-notes"></div>

<div id="quiz-${lecture.id}" class="ai-quiz"></div>
</div>
    `).join("");
}

async function addLecture() {
    const title = document.getElementById("lectureTitle").value.trim();
    const subject = document.getElementById("lectureSubject").value.trim();
    const lectureDate = document.getElementById("lectureDate").value;
    const videoUrl = document.getElementById("lectureVideo").value.trim();
    const notes = document.getElementById("lectureNotes").value.trim();

    if (!title || !subject || !lectureDate) {
        alert("Please fill lecture title, subject and date.");
        return;
    }

    const response = await fetch("/api/lectures", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: title,
            subject: subject,
            lecture_date: lectureDate,
            video_url: videoUrl,
            notes: notes
        })
    });

    const result = await response.json();

    if (!response.ok) {
        alert(result.error || "Could not add lecture.");
        return;
    }

    document.getElementById("lectureTitle").value = "";
    document.getElementById("lectureSubject").value = "";
    document.getElementById("lectureDate").value = "";
    document.getElementById("lectureVideo").value = "";
    document.getElementById("lectureNotes").value = "";

    loadLectures();
}

async function deleteLecture(id) {
    if (!confirm("Are you sure you want to delete this lecture?")) {
        return;
    }

    await fetch(`/api/lectures/${id}`, {
        method: "DELETE"
    });

    loadLectures();
}


async function generateNotes(id) {
    const box = document.getElementById(`notes-${id}`);

    box.innerHTML = "🤖 Generating AI notes... Please wait.";

    const response = await fetch(`/api/lectures/${id}/notes`, {
        method: "POST"
    });

    const result = await response.json();

    if (!response.ok) {
        box.innerHTML = "❌ " + (result.error || "Could not generate notes.");
        return;
    }

    box.innerHTML = `
        <hr>
        <h3>📄 AI Generated Notes</h3>
        <div>${escapeHtml(result.notes).replace(/\n/g, "<br>")}</div>
    `;
}
async function generateQuiz(id) {
    const box = document.getElementById(`quiz-${id}`);

    box.innerHTML = "🤖 Generating AI quiz... Please wait.";

    const response = await fetch(`/api/lectures/${id}/quiz`, {
        method: "POST"
    });

    const result = await response.json();

    if (!response.ok) {
        box.innerHTML = "❌ " + (result.error || "Could not generate quiz.");
        return;
    }

    box.innerHTML = `
        <hr>
        <h3>🧠 AI Generated Quiz</h3>
        <div>${escapeHtml(result.quiz).replace(/\n/g, "<br>")}</div>
    `;
}

document.addEventListener("DOMContentLoaded", () => {
    loadLectures();
});

