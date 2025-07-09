function getAuthHeaders() {
  return {
    "Authorization": "Bearer " + sessionStorage.getItem("access"),
    "Content-Type": "application/json"
  };
}