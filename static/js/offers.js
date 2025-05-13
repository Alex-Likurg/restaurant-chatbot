let tg = window.Telegram.WebApp;
tg.expand();

document.addEventListener("DOMContentLoaded", function () {
    let tg = window.Telegram.WebApp;
    tg.expand();

    // Кнопка "Дневной Бонус"
    document.getElementById("dayBonus").addEventListener("click", function () {
        fetch("https://krasnayazvezda.store/api/specials/day_bonus")
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    let img = document.createElement("img");
                    img.src = data.image_url;
                    img.alt = "Дневной Бонус";
                    img.style.width = "80%";
                    document.getElementById("offers").appendChild(img);
                } else {
                    alert("Ошибка: " + data.message);
                }
            })
            .catch(error => console.error("Ошибка при получении дневного бонуса:", error));
    });

    // Кнопка "Персональный Бонус"
    document.getElementById("personalBonus").addEventListener("click", function () {
        let user_id = tg.initDataUnsafe?.user?.id;
        if (!user_id) {
            alert("Ошибка: невозможно получить ID пользователя!");
            return;
        }

        fetch("https://krasnayazvezda.store/api/specials/personal_bonus", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: user_id })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
            })
            .catch(error => console.error("Ошибка при получении персонального бонуса:", error));
    });
});


