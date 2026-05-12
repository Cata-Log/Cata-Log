document.querySelectorAll(".delete-provider-button").forEach((deleteButton) => {
  deleteButton.addEventListener("click", (event) => {
    provider_id = event.target.dataset.id;
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
    updateButton.addEventListener("click", (event) => {
      provider_id = event.target.dataset.id;
      updateRequest = new Request(`/api/v1/providers/${provider_id}/job/run`, {
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

document.querySelectorAll(".provider-job-switch").forEach((jobSwitch) => {
  jobSwitch.addEventListener("change", (event) => {
    provider_id = event.target.dataset.id;
    endpoint = event.target.checked ? "add" : "remove";
    toggleRequest = new Request(
      `/api/v1/providers/${provider_id}/job/${endpoint}`,
      {
        method: "POST",
      },
    );
    fetch(toggleRequest)
      .then((response) => {
        if (response.ok) {
          jobSwitch.blur();
        } else {
          console.error(`Error toggling job for provider ${provider_id}`);
        }
      })
      .catch((e) => console.error(e));
  });
});
