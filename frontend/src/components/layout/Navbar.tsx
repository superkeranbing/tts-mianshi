import { Link, useLocation } from "react-router-dom";
import { useAppStore } from "../../stores/appStore";

export default function Navbar() {
  const { user, logout } = useAppStore();
  const loc = useLocation();

  const links = [
    { to: "/", label: "首页" },
    { to: "/history", label: "历史记录" },
    { to: "/interview", label: "面试分析" },
  ];

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-6">
        <Link to="/" className="text-lg font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
          🎙 听记面试
        </Link>
        <div className="flex gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-3 py-1.5 rounded text-sm transition-colors ${
                loc.pathname === l.to ? "bg-gray-800 text-emerald-400" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-4">
        {user ? (
          <>
            <span className="text-sm text-gray-400">👤 {user.username}</span>
            <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
              退出
            </button>
          </>
        ) : (
          <Link to="/login" className="text-sm px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded text-white transition-colors">
            登录
          </Link>
        )}
      </div>
    </nav>
  );
}
