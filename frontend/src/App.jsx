import { Routes, Route } from "react-router-dom";
import { SettingsProvider } from "./Context/SettingsContext";

// Pages
import Home from "./Pages/Home";
import DangNhap from "./Pages/Dang_nhap";
import DangKy from "./Pages/Dang_ky";
import ForgotPassword from "./Pages/Forgot_password";
import ResetPassword from "./Pages/Reset_password";

// Admin
import HomeAdmin from "./Admin/Home_Admin";
import DanhGiaNangLucAdmin from "./Admin/Danh_gia_nang_luc_Admin";
import QuanLyBaiKiemTraAdmin from "./Admin/Quan_ly_bai_kiem_tra_Admin";
import CloKyNangAdmin from "./Admin/CLO_Ky_nang_Admin";
import DanhGiaAiAdmin from "./Admin/Danh_gia_AI_Admin";
import TNAdmin from "./Admin/TN_Admin";
import SQLAdmin from "./Admin/SQL_Admin";
import TLAdmin from "./Admin/TL_Admin";
import BaoCaoAdmin from "./Admin/Bao_cao_Admin";
import CaiDatAdmin from "./Admin/Cai_dat_Admin";
import XemLaiBaiKiemTraAdmin from "./Admin/Xem_lai_bai_kiem_tra_Admin";
import XepHang from "./Admin/Xep_hang_Admin";
import HoSoThanhVienAdmin from "./Admin/Ho_so_thanh_vien_Admin";
import ChiTietCloAdmin from "./Admin/Chi_tiet_CLO_Admin";

// Learner
import HomeLearner from "./Learner/Home_Learner";
import PhanTichLearner from "./Learner/Phan_tich_Learner";
import XemLaiBaiLearner from "./Learner/Xem_lai_bai_Learner";
import TNLearner from "./Learner/TN_Learner";
import SQLLearner from "./Learner/SQL_Learner";
import TLLearner from "./Learner/TL_Learner";

export default function App() {
  return (
    <SettingsProvider>
      <Routes>
        {/* Pages */}
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
          element={
            <ForgotPassword
              loginHref="/Dang_nhap"
              resetHref="/Reset_password"
              demoMode={true}
            />
          }
        />

        <Route
          path="/Reset_password"
          element={
            <ResetPassword loginHref="/Dang_nhap" />
          }
        />

        {/* Admin */}
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
          path="/SQL_Admin"
          element={<SQLAdmin />}
        />

        <Route
          path="/TL_Admin"
          element={<TLAdmin />}
        />

        <Route
          path="/Bao_cao_Admin"
          element={<BaoCaoAdmin />}
        />

        <Route
          path="/Cai_dat_Admin"
          element={<CaiDatAdmin />}
        />

        <Route
          path="/Xem_lai_bai_kiem_tra_Admin/:examId"
          element={<XemLaiBaiKiemTraAdmin />}
        />

        <Route
          path="/Xep_hang_Admin"
          element={<XepHang />}
        />

        <Route
          path="/Ho_so_thanh_vien_Admin/:studentId"
          element={<HoSoThanhVienAdmin />}
        />

        <Route
          path="/Chi_tiet_CLO_Admin/:studentId"
          element={<ChiTietCloAdmin />}
        />

        {/* Learner */}
        <Route
          path="/Home_Learner"
          element={<HomeLearner />}
        />

        <Route
          path="/Phan_tich_Learner"
          element={<PhanTichLearner />}
        />

        <Route
          path="/Xem_lai_bai_Learner"
          element={<XemLaiBaiLearner />}
        />

        <Route
          path="/TN_Learner"
          element={<TNLearner />}
        />

        <Route
          path="/SQL_Learner"
          element={<SQLLearner />}
        />

        <Route
          path="/TL_Learner"
          element={<TLLearner />}
        />
      </Routes>
    </SettingsProvider>
  );
}