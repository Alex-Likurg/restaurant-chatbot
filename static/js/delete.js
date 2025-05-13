let tg = window.Telegram.WebApp;
document.getElementById("deleteButton").addEventListener("click", function () {
    let tg = window.Telegram.WebApp;
    let user_id = tg.initDataUnsafe?.user?.id;
    let reservation_id = document.getElementById("number").value;

    if (!user_id) {
        alert("Ошибка: невозможно получить ID пользователя!");
        return;
    }

    if (!reservation_id) {
        alert("Ошибка: Введите номер резервации!");
        return;
    }

    let data = {
        user_id: user_id,
        number: reservation_id
    };

    fetch("https://krasnayazvezda.store/api/delete_table", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            if (result.status === "success") {
                alert("✅ Резервация успешно удалена!");
                tg.close(); // Закрываем Web App
            } else {
                alert("Ошибка удаления: " + result.message);
            }
        })
        .catch(error => {
            console.error("Ошибка при отправке запроса:", error);
            alert("Ошибка при отправке запроса!");
        });
});

