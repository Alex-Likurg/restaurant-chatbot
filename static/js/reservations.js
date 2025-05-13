let tg = window.Telegram.WebApp;
tg.expand();

function loadReservations() {
    let user_id = tg.initDataUnsafe?.user?.id;
    if (!user_id) {
        alert("Ошибка: невозможно получить ID пользователя!");
        return;
    }

    fetch("https://krasnayazvezda.store/api/get_reservations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user_id })
    })
    .then(response => response.json())
    .then(data => {
        let reservationsDiv = document.getElementById("reservations");
        reservationsDiv.innerHTML = "";

        if (data.status === "success") {
            data.reservations.forEach(reservation => {
                let div = document.createElement("div");
                div.className = "reservation";
                div.innerHTML = `<h3>${reservation.date} ${reservation.time}</h3>
                                 <p>👥 ${reservation.guests} гостей</p>
                                 <p>📝 Бронь на имя: ${reservation.name}</p>`;
                reservationsDiv.appendChild(div);
            });
        } else {
            reservationsDiv.innerHTML = `<p>❌ У вас пока нет активных резерваций.</p>`;
        }
    })
    .catch(error => {
        console.error("Ошибка загрузки резерваций:", error);
    });
}

document.addEventListener("DOMContentLoaded", loadReservations);
