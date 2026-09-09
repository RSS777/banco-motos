self.addEventListener("push", (event) => {
  const text = event.data ? event.data.text() : "Rodada diária concluída.";
  event.waitUntil(
    self.registration.showNotification("banco-motos", { body: text })
  );
});
