document.getElementById("config-form").addEventListener("submit", (event) => {
  event.preventDefault();
  form = new FormData(event.target);
  request = new Request("/api/v1/config", {
    method: "POST",
    headers: new Headers({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({
      name: form.get("name"),
      value: form.get("value"),
    }),
  });
  fetch(request).then((response) => {
    if (response.status === 201) {
      window.location.reload();
    } else {
      response.json().then((json) => {
        errorElement = event.target.querySelector("#form-error");
        errorElement.innerHTML =
          json.detail || json.message || "An unknown error occurred";
      });
    }
  });
});
