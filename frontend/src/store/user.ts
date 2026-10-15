import { defineStore } from "pinia";
import { ref } from "vue";
import { login as apiLogin, register as apiRegister, fetchMe, updateUsername as apiUpdateUsername } from "@/api/modules";

export const useUserStore = defineStore("user", () => {
  const token = ref<string>(localStorage.getItem("yisu_token") || "");
  const username = ref<string>(localStorage.getItem("yisu_username") || "");
  const role = ref<string>(localStorage.getItem("yisu_role") || "user");
  const avatar = ref<string>(localStorage.getItem("yisu_avatar") || "");
  const email = ref<string>(localStorage.getItem("yisu_email") || "");

  function saveAvatar(url: string) {
    avatar.value = url;
    if (url) localStorage.setItem("yisu_avatar", url);
    else localStorage.removeItem("yisu_avatar");
  }

  async function updateUsername(name: string) {
    const data = await apiUpdateUsername(name);
    username.value = data.username;
    localStorage.setItem("yisu_username", data.username);
    return data;
  }

  async function login(name: string, password: string) {
    const data = await apiLogin(name, password);
    token.value = data.token;
    username.value = data.username;
    role.value = data.role;
    email.value = data.email || "";
    localStorage.setItem("yisu_token", data.token);
    localStorage.setItem("yisu_username", data.username);
    localStorage.setItem("yisu_role", data.role);
    if (email.value) localStorage.setItem("yisu_email", email.value);
  }

  async function register(name: string, password: string, email2: string) {
    const data = await apiRegister(name, password, email2);
    token.value = data.token;
    username.value = data.username;
    role.value = data.role;
    email.value = data.email || email2;
    localStorage.setItem("yisu_token", data.token);
    localStorage.setItem("yisu_username", data.username);
    localStorage.setItem("yisu_role", data.role);
    if (email.value) localStorage.setItem("yisu_email", email.value);
  }

  async function loadMe() {
    if (!token.value) return;
    try {
      const me = await fetchMe();
      saveAvatar(me.avatar || "");
      username.value = me.username;
      role.value = me.role;
      email.value = me.email || "";
      if (email.value) localStorage.setItem("yisu_email", email.value);
    } catch {
      logout();
    }
  }

  function logout() {
    token.value = "";
    username.value = "";
    role.value = "user";
    email.value = "";
    saveAvatar("");
    localStorage.removeItem("yisu_token");
    localStorage.removeItem("yisu_username");
    localStorage.removeItem("yisu_role");
    localStorage.removeItem("yisu_email");
  }

  return { token, username, role, avatar, email, saveAvatar, updateUsername, login, register, logout, loadMe };
});
