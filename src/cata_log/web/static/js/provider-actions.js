document.querySelectorAll(".delete-provider-button").forEach((deleteButton) => {
  deleteButton.addEventListener("click", () => {
    provider_id = this.dataset.id;
    deleteRequest = new Request(`/api/v1/providers/${provider_id}`, {
      method: "DELETE",
    });
    fetch(deleteRequest)
      .then((response) => {
        if (response.ok) {
          window.location.reload();
        } else {
          console.error(`Deleting provider ${provider_id} failed`);
        }
      })
      .catch((e) => console.error(e));
  });
});
document
  .querySelectorAll(".schedule-provider-update-button")
  .forEach((updateButton) => {
    updateButton.addEventListener("click", () => {
      provider_id = this.dataset.id;
      updateRequest = new Request(`/api/v1/providers/${provider_id}/update`, {
        method: "POST",
      });
      fetch(updateRequest)
        .then((response) => {
          if (response.ok) {
            updateButton.blur();
          } else {
            console.error(
              `Error scheduling update for provider ${provider_id}`,
            );
          }
        })
        .catch((e) => console.error(e));
    });
  });
