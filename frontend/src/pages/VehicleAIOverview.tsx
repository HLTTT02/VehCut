import { useEffect, useRef, useState } from "react";
import { AlertTriangle, BellRing, Camera, Car, CheckCircle2, ChevronDown, CircleAlert, Clock3, Download, Eye, FileVideo, Filter, Fullscreen, History, MoreVertical, Pause, Play, ShieldAlert, Upload, Volume2 } from "lucide-react";
import { api } from "../api/client";
import type { ModulePage } from "./VehicleAIModulePage";

type Props = { onNavigate: (page: ModulePage) => void };
const roadImage = "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1600&q=86";
const objects = [
  ["#012", "Truck", "29H-123.45", "Có biển", "blue"], ["#005", "Car", "30A-678.90", "Có biển", "red"],
  ["#018", "Motorcycle", "Không rõ", "Không biển", "orange"], ["#021", "Car", "--", "Không phát hiện biển", "purple"], ["#026", "Car", "29A-555.66", "Có biển", "green"],
] as const;
const alerts = [["Bike #18", "Không biển", "14:02", "red"], ["Car #09", "Lảng vãng", "13:57", "orange"], ["Car #07", "Không biển", "13:42", "red"], ["Truck #03", "Quay lại", "13:20", "purple"], ["Motorcycle #15", "Lảng vãng", "12:56", "orange"]] as const;

export function VehicleAIOverview({ onNavigate }: Props) {
  const [tab, setTab] = useState<"objects" | "clips">("objects");
  const uploadRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewIsImage, setPreviewIsImage] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("READY");
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);
  useEffect(() => {
    const button = document.querySelector<HTMLButtonElement>(".vo-source button:first-of-type");
    const openUploader = (event: MouseEvent) => { event.preventDefault(); uploadRef.current?.click(); };
    button?.addEventListener("click", openUploader);
    return () => button?.removeEventListener("click", openUploader);
  }, []);
  useEffect(() => {
    const container = document.querySelector<HTMLElement>(".vo-video");
    const fallback = container?.querySelector<HTMLImageElement>("img");
    if (!container || !fallback) return;
    const existing = container.querySelector<HTMLElement>(".vo-preview-media");
    existing?.remove();
    fallback.style.display = "none";
    const media = previewUrl ? document.createElement(previewIsImage ? "img" : "video") : document.createElement("div");
    media.className = "vo-preview-media";
    if (previewUrl && (media instanceof HTMLImageElement || media instanceof HTMLMediaElement)) { media.src = previewUrl; if (media instanceof HTMLVideoElement) media.controls = true; }
    if (!previewUrl) { media.textContent = "Chọn Upload video/image để xem nội dung tại đây"; }
    container.prepend(media);
  }, [previewUrl, previewIsImage]);
  const choosePreview = async (file?: File) => {
    if (!file) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewIsImage(file.type.startsWith("image/"));
    setPreviewUrl(URL.createObjectURL(file));
    setUploadStatus("UPLOADING");
    try { await api.uploadVideo(file); setUploadStatus("UPLOADED"); }
    catch { setUploadStatus("UPLOAD ERROR"); }
  };
  return <div className="vo-page">
    <section className="vo-topbar"><input ref={uploadRef} className="vo-upload-input" type="file" accept="video/mp4,video/quicktime,video/x-msvideo,image/jpeg,image/png,image/webp" onChange={(event) => { void choosePreview(event.target.files?.[0]); }}/>
      <div className="vo-head"><h1>Phát hiện phương tiện khả nghi</h1><p>Phát hiện xe không biển, lảng vãng, quay lại, xuất hiện nhiều lần...</p></div>
      <div className="vo-source"><small>Nguồn dữ liệu</small><div><button onClick={() => onNavigate("analysis")}><FileVideo />Video Upload</button><button className="active" onClick={() => onNavigate("camera")}><Camera />Camera Live</button></div></div>
      <div className="vo-select"><small>Camera</small><button onClick={() => onNavigate("camera")}>Cổng chính <i>● ONLINE</i><ChevronDown /></button></div>
      <div className="vo-select vo-date"><small>Thời gian</small><button><Clock3 />2025-06-10 09:00 <b>→</b> 2025-06-10 12:00 <ChevronDown /></button></div>
    </section>

    <section className="vo-core">
      <div className="vo-left">
        <div className="vo-video"><img src={roadImage} alt="Camera giám sát giao thông" /><div className="vo-camera-tag"><b>● LIVE</b> Cổng chính - 192.168.1.10</div><time>2025-06-10&nbsp; 09:24:17</time>
          <span className="vo-box truck"><b>#012&nbsp; Truck</b></span><span className="vo-box car"><b>#005&nbsp; Car</b></span><span className="vo-box bike"><b>#018&nbsp; Motorcycle</b></span><span className="vo-box purple"><b>#021&nbsp; Car</b><em>Chưa phát hiện biển</em></span>
          <footer><Pause /><div className="vo-range"><i /></div><strong>00:02:14&nbsp; / 00:05:00</strong><Volume2 /><button>1.0x <ChevronDown /></button><Fullscreen /></footer>
        </div>
        <div className="vo-object-panel"><header><div><button className={tab === "objects" ? "active" : ""} onClick={() => setTab("objects")}>Đối tượng phát hiện</button><button className={tab === "clips" ? "active" : ""} onClick={() => setTab("clips")}>Danh sách clip</button></div><button className="vo-more"><MoreVertical /></button></header>
          {tab === "objects" ? <div className="vo-objects">{objects.map(([id, kind, plate, status, tone]) => <article key={id} className={tone}><img src={roadImage} alt="Phương tiện được phát hiện" /><div><b>{id}</b><span>{kind}</span><MoreVertical /><small>{plate}</small><em>{status}</em><time>09:18:32</time></div></article>)}</div> : <div className="vo-empty"><FileVideo /><p>Clip của các đối tượng sẽ hiển thị tại đây.</p><button onClick={() => onNavigate("review")}>Mở QC Review</button></div>}
          <footer className="vo-filters"><button><Filter />Bộ lọc</button><button className="active">Tất cả</button><button className="danger">◉ Không biển</button><button className="warning">◔ Lảng vãng</button><button className="purple">◉ Quay lại</button><button className="blue">◉ Nhiều lần</button><button className="download" onClick={() => onNavigate("review")}><Download />Tải clip đã chọn (3)</button></footer>
        </div>
      </div>
      <div className="vo-events"><h2>Phát hiện sự kiện</h2><ul><li><Car />Tổng số xe <b>28</b></li><li className="red"><CircleAlert />Không biển <b>3</b></li><li className="orange"><Clock3 />Lảng vãng <b>2</b></li><li className="purple"><History />Quay lại <b>1</b></li><li className="blue"><History />Xuất hiện nhiều lần <b>0</b></li></ul><div className="vo-active-alert"><BellRing /><span>Đang cảnh báo</span><b>2</b></div></div>
    </section>

    <aside className="vo-right">
      <section className="vo-quick"><h2>Thống kê nhanh</h2><div><div className="vo-donut"><b>28</b><small>Tổng số xe</small></div><ul><li className="blue">Car <b>12 (43%)</b></li><li className="green">Motorcycle <b>10 (36%)</b></li><li className="orange">Truck <b>4 (14%)</b></li><li className="purple">Bus <b>2 (7%)</b></li></ul></div><footer><span className="red"><b>3</b>Không biển</span><span className="orange"><b>2</b>Lảng vãng</span><span className="green"><b>0</b>FP/FN</span></footer></section>
      <section className="vo-alerts"><header><h2>Cảnh báo gần đây</h2><button onClick={() => onNavigate("review")}>Xem tất cả</button></header>{alerts.map(([name, reason, time, tone]) => <article key={`${name}-${time}`}><img src={roadImage} alt="Ảnh cảnh báo" /><div><b>{time}</b><small>{name}</small><em className={tone}>{reason}</em></div><button onClick={() => onNavigate("review")}>Xem clip</button></article>)}</section>
    </aside>
  </div>;
}
