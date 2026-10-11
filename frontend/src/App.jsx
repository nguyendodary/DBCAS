import { Routes, Route } from "react-router-dom";

import Home from "./Pages/Home";
import DangNhap from "./Pages/Dang_nhap";
import DangKy from "./Pages/Dang_ky";
import ForgotPassword from "./Pages/Forgot_password";
import HomeAdmin from "./Admin/Home_Admin";
import DanhGiaNangLucAdmin from "./Admin/Danh_gia_nang_luc_Admin";
import QuanLyBaiKiemTraAdmin from "./Admin/Quan_ly_bai_kiem_tra_Admin";
import CloKyNangAdmin from "./Admin/CLO_Ky_nang_Admin";
import DanhGiaAiAdmin from "./Admin/Danh_gia_AI_Admin";
import TNAdmin from "./Admin/TN_Admin";
import ResetPassword from "./Pages/Reset_password";

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Home
            loginHref="/Dang_nhap"
            registerHref="/Dang_ky"
          />
        }
      />

      <Route
        path="/Dang_nhap"
        element={
          <DangNhap
            demoMode={true}
            adminHref="/Home_Admin"
            learnerHref="/Home_Learner"
            registerHref="/Dang_ky"
            forgotHref="/Forgot_password"
            homeHref="/"
          />
        }
      />

      <Route
        path="/Dang_ky"
        element={<DangKy />}
      />

      <Route
        path="/Forgot_password"
        element={<ForgotPassword loginHref="/Dang_nhap" />}
      />

      <Route
        path="/Home_Admin"
        element={<HomeAdmin />}
      />

      <Route
        path="/Danh_gia_nang_luc_Admin"
        element={<DanhGiaNangLucAdmin />}
      />

      <Route
        path="/Quan_ly_bai_kiem_tra_Admin"
        element={<QuanLyBaiKiemTraAdmin />}
      />

      <Route
        path="/CLO_Ky_nang_Admin"
        element={<CloKyNangAdmin />}
      />

      <Route
        path="/Danh_gia_AI_Admin"
        element={<DanhGiaAiAdmin />}
      />

      <Route
        path="/TN_Admin"
        element={<TNAdmin />}
      />

      <Route
        path="/Home_Learner"
        element={<p>Trang chủ người học đang được xây dựng.</p>}
      />

      <Route
        path="*"
        element={<p>Không tìm thấy trang.</p>}
      />

      <Route
  path="/Forgot_password"
  element={
    <ForgotPassword
      loginHref="/Dang_nhap"
      resetHref="/Reser_password"
      demoMode={true}
    />
  }
/>

<Route
  path="/Reset_password"
  element={<ResetPassword loginHref="/Dang_nhap" />}
/>
    </Routes>
  );
}