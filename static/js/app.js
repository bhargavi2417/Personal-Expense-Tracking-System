// Small helpers: confirm before destructive actions, and basic client-side checks.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form.js-confirm").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  var amount = document.getElementById("amount");
  if (amount) {
    amount.addEventListener("input", function () {
      var value = parseFloat(amount.value);
      if (amount.value !== "" && (isNaN(value) || value <= 0)) {
        amount.setCustomValidity("Amount must be greater than zero.");
      } else {
        amount.setCustomValidity("");
      }
    });
  }

  var reset = document.getElementById("reset-filters");
  if (reset) {
    reset.addEventListener("click", function () {
      window.location.href = reset.getAttribute("data-url");
    });
  }
});
