let tg = window.Telegram.WebApp;
tg.expand();

document.addEventListener("DOMContentLoaded", function () {
    if (window.Telegram && window.Telegram.WebApp) {
        console.log("✅ Telegram API загружен!");
        Telegram.WebApp.expand();
    } else {
        console.log("❌ Telegram API не загружен!");
        alert("Ошибка: Откройте Web App в Telegram, а не в браузере!");
    }
});

document.getElementById("bookButton").addEventListener("click", function () {
    let user_id = tg.initDataUnsafe?.user?.id;
    if (!user_id) {
        alert("Ошибка: невозможно получить ID пользователя!");
        return;
    }

    let data = {
        user_id: user_id,
        date: document.getElementById("date").value,
        time: document.getElementById("time").value,
        guests: document.getElementById("guests").value,
        name: document.getElementById("name").value,
        surname: document.getElementById("surname").value,
        phone: document.getElementById("phone").value
    };

    fetch("https://krasnayazvezda.store/api/book_table", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === "success") {
            alert("✅ Столик забронирован!");
            tg.close();
        } else {
            alert("Ошибка бронирования: " + result.message);
        }
    })
    .catch(error => {
        alert("Ошибка при отправке запроса!");
    });
});
