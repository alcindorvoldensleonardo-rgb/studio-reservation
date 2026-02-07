const times = ["10:00", "12:00", "14:00", "16:00", "18:00"];
let selectedTime = null;
let selectedDate = null;

async function loadCalendar() {
    selectedDate = document.getElementById("date").value;
    const calendar = document.getElementById("calendar");
    calendar.innerHTML = "";
    selectedTime = null;
    disableButton();

    if (!selectedDate) return;

    const res = await fetch("/api/calendar");
    const bookedSlots = await res.json();

    times.forEach(time => {
        const div = document.createElement("div");
        div.innerText = time;
        div.classList.add("time-slot");

        const isBooked = bookedSlots.some(
            r => r[0] === selectedDate && r[1] === time
        );

        if (isBooked) {
            div.classList.add("time-booked");
        } else {
            div.classList.add("time-free");
            div.onclick = () => selectTime(div, time);
        }

        calendar.appendChild(div);
    });
}

function selectTime(element, time) {
    document.querySelectorAll(".time-slot").forEach(el =>
        el.classList.remove("time-selected")
    );

    element.classList.add("time-selected");
    selectedTime = time;

    document.getElementById("formDate").value = selectedDate;
    document.getElementById("formTime").value = selectedTime;

    enableButton();
}

function enableButton() {
    const btn = document.getElementById("confirmBtn");
    btn.disabled = false;
    btn.style.opacity = "1";
    btn.style.cursor = "pointer";
}

function disableButton() {
    const btn = document.getElementById("confirmBtn");
    btn.disabled = true;
    btn.style.opacity = "0.5";
    btn.style.cursor = "not-allowed";
}

document.getElementById("date").addEventListener("change", loadCalendar);
