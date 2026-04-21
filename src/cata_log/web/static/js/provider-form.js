document.getElementById("provider-form").addEventListener("submit", (event) => {
  event.preventDefault();
  form = new FormData(event.target);
  request = new Request("/api/v1/providers", {
    method: "POST",
    headers: new Headers({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({
      class_id: form.get("class_id"),
      configuration: JSON.parse(form.get("configuration")),
    }),
  });
  fetch(request).then((response) => {
    if (response.status === 201) {
      window.location.reload();
    } else {
      response.json().then((json) => {
        errorElement = this.querySelector("#form-error");
        errorElement.innerHTML =
          json.detail || json.message || "An unknown error occurred";
      });
    }
  });
});
