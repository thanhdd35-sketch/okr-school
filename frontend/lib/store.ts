import { create } from "zustand";

interface NguoiDung {
  id: string;
  email: string;
  vai_tro: string;
  ho_ten: string;
  ten_lop?: string;
  ho_ten_con?: string;
  hoc_sinh_id?: string;
}

interface AppStore {
  nguoiDung: NguoiDung | null;
  token: string | null;
  datNguoiDung: (nd: NguoiDung, token: string) => void;
  dangXuat: () => void;
  khoiTao: () => void;
}

export const useStore = create<AppStore>((set) => ({
  nguoiDung: null,
  token: null,

  datNguoiDung: (nd, token) => {
    localStorage.setItem("okr_token", token);
    localStorage.setItem("okr_user", JSON.stringify(nd));
    set({ nguoiDung: nd, token });
  },

  dangXuat: () => {
    localStorage.removeItem("okr_token");
    localStorage.removeItem("okr_user");
    set({ nguoiDung: null, token: null });
  },

  khoiTao: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("okr_token");
    const user = localStorage.getItem("okr_user");
    if (token && user) {
      set({ token, nguoiDung: JSON.parse(user) });
    }
  },
}));
