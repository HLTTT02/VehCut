import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, Bell, Camera, Car, Check, CheckSquare, ChevronDown,
  Clock3, Eye, FileVideo, History, Home, RefreshCw, ScanLine, Settings,
  Play, ShieldAlert, Upload, Video, X
} from "lucide-react";
import { api } from "../api/client";
import type { Clip, JobHistory, Statistics, VehicleTrack } from "../types/api";
import { VehicleAIOverview } from "./VehicleAIOverview";

export type ModulePage = "overview" | "analysis" | "camera" | "alerts" | "review" | "history" | "statistics" | "settings";
type NavigatePage = ModulePage;
type ReviewItem = { clip: Clip; track?: VehicleTrack; filename?: string };

const emptyStats: Statistics = { total_videos:0,total_vehicles:0,total_clips:0,pending_review:0,completed_jobs:0,failed_jobs:0,vehicle_classes:{car:0,motorcycle:0,truck:0,bus:0} };
const pageMeta: Record<ModulePage,{title:string;description:string}> = {
  overview:{title:"Giám sát video",description:"Theo dõi phương tiện và sự kiện cần xem xét trong thời gian thực."},
  analysis:{title:"Phân tích video",description:"Tải video, theo dõi tiến độ và xem phương tiện được phát hiện."},
  camera:{title:"Camera Live",description:"Quản lý nguồn camera và trạng thái kết nối."},
  alerts:{title:"Cảnh báo realtime",description:"Các sự kiện cần người vận hành kiểm tra."},
  review:{title:"QC Review",description:"Xác nhận hoặc loại bỏ clip được hệ thống gắn cờ."},
  history:{title:"Lịch sử xử lý",description:"Theo dõi toàn bộ job đã chạy trên hệ thống."},
  statistics:{title:"Thống kê",description:"Số liệu tổng hợp trực tiếp từ dữ liệu đã lưu."},
  settings:{title:"Cài đặt",description:"Cấu hình ngưỡng phân tích và chính sách cảnh báo."},
};

export function VehicleAIModulePage({page,onNavigate}:{page:ModulePage;onNavigate:(page:NavigatePage)=>void}) {
  const [history,setHistory] = useState<JobHistory[]>([]);
  const [statistics,setStatistics] = useState<Statistics>(emptyStats);
  const [reviewItems,setReviewItems] = useState<ReviewItem[]>([]);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState<string|null>(null);
  const [preview,setPreview] = useState<Clip|null>(null);

  useEffect(()=>{
    let active=true;
    if(page==="overview") { setLoading(false); setError(null); return ()=>{active=false}; }
    const load=async()=>{
      setLoading(true);setError(null);
      try{
        const [jobs,summary]=await Promise.all([api.getHistory(),api.getStatistics()]);
        if(!active)return;
        setHistory(jobs);setStatistics(summary);
        if(page==="review"||page==="alerts"){
          const completed=jobs.filter(job=>job.status==="COMPLETED").slice(0,20);
          const groups=await Promise.all(completed.map(async job=>{
            const [clips,tracks]=await Promise.all([api.getClips(job.video_id),api.getTracks(job.video_id)]);
            return clips.map(clip=>({clip,track:tracks.find(track=>track.id===clip.vehicle_track_id),filename:job.filename??undefined}));
          }));
          if(active)setReviewItems(groups.flat());
        }
      }catch(reason){if(active)setError(reason instanceof Error?reason.message:"Không thể tải dữ liệu");}
      finally{if(active)setLoading(false);}
    };
    load();return()=>{active=false};
  },[page]);

  const pending=useMemo(()=>reviewItems.filter(item=>item.clip.status==="NEEDS_REVIEW"),[reviewItems]);
  const decide=async(item:ReviewItem,status:"APPROVED"|"REJECTED")=>{
    try{const updated=await api.reviewClip(item.clip.id,{status,reason:"QC manual review"});setReviewItems(items=>items.map(current=>current.clip.id===updated.id?{...current,clip:updated}:current));}
    catch(reason){setError(reason instanceof Error?reason.message:"Không thể lưu quyết định review");}
  };
  const meta=pageMeta[page];

  return <div className="vam-shell">
    <header className="vam-header"><div className="vam-brand"><span><Eye/></span><div><b>VehicleAI</b><small>Phát hiện phương tiện khả nghi</small></div></div><div className="vam-account"><Bell/><span>V</span><b>Vanth</b><ChevronDown/></div></header>
    <aside className="vam-sidebar"><nav>
      <button className={page==="overview"?"active":""} onClick={()=>onNavigate("overview")}><Home/>Tổng quan</button>
      <button className={page==="analysis"?"active":""} onClick={()=>onNavigate("analysis")}><Upload/>Phân tích video</button>
      <button className={page==="camera"?"active":""} onClick={()=>onNavigate("camera")}><Video/>Camera Live</button>
      <button className={page==="alerts"?"active":""} onClick={()=>onNavigate("alerts")}><ShieldAlert/>Cảnh báo</button>
      <button className={page==="review"?"active":""} onClick={()=>onNavigate("review")}><CheckSquare/>QC Review</button>
      <button className={page==="history"?"active":""} onClick={()=>onNavigate("history")}><History/>Lịch sử</button>
      <button className={page==="statistics"?"active":""} onClick={()=>onNavigate("statistics")}><Activity/>Thống kê</button>
      <button className={page==="settings"?"active":""} onClick={()=>onNavigate("settings")}><Settings/>Cài đặt</button>
    </nav><div className="vam-system"><i/><div><b>Backend đã kết nối</b><small>Dữ liệu lấy qua REST API</small></div></div></aside>
    <main className="vam-main">{page==="overview"?<VehicleAIOverview onNavigate={onNavigate}/>:<><div className="vam-page-head"><div><button onClick={()=>onNavigate("overview")}>← Tổng quan</button><h1>{meta.title}</h1><p>{meta.description}</p></div><button className="vam-refresh" onClick={()=>location.reload()}><RefreshCw/>Làm mới</button></div>
      {error&&<div className="vam-error"><AlertTriangle/>{error}</div>}
      {loading?<div className="vam-loading"><RefreshCw/>Đang tải dữ liệu…</div>:<ModuleContent page={page} history={history} statistics={statistics} pending={pending} preview={setPreview} decide={decide}/>} </>}
    </main>
    {preview&&<div className="vam-modal"><div><header><b>Xem clip</b><button onClick={()=>setPreview(null)}><X/></button></header><video controls autoPlay src={api.fileUrl(preview.full_clip_path)}/></div></div>}
  </div>;
}

function ModuleContent({page,history,statistics,pending,preview,decide}:{page:ModulePage;history:JobHistory[];statistics:Statistics;pending:ReviewItem[];preview:(clip:Clip)=>void;decide:(item:ReviewItem,status:"APPROVED"|"REJECTED")=>void}) {
  if(page==="analysis") return <AnalysisPanel preview={preview}/>;
  if(page==="statistics") return <><div className="vam-kpi-row"><Kpi icon={<FileVideo/>} label="Video" value={statistics.total_videos}/><Kpi icon={<Car/>} label="Phương tiện" value={statistics.total_vehicles}/><Kpi icon={<Video/>} label="Clip" value={statistics.total_clips}/><Kpi icon={<ShieldAlert/>} label="Cần review" value={statistics.pending_review}/></div><section className="vam-panel"><h2>Phân bố phương tiện</h2><div className="vam-class-grid">{Object.entries(statistics.vehicle_classes).map(([name,value])=><div key={name}><span>{name}</span><b>{value}</b></div>)}</div></section></>;
  if(page==="history") return <section className="vam-panel"><h2>Job xử lý gần đây</h2>{history.length?<div className="vam-table"><div className="head"><span>Video</span><span>Trạng thái</span><span>Tiến độ</span><span>Hoàn tất</span></div>{history.map(job=><div key={job.id}><span><FileVideo/>{job.filename??job.video_id}</span><span className={`state ${job.status.toLowerCase()}`}>{job.status}</span><span>{job.progress}%</span><span>{job.completed_at?new Date(job.completed_at).toLocaleString("vi-VN"):"--"}</span></div>)}</div>:<Empty icon={<History/>} title="Chưa có lịch sử" text="Hãy phân tích một video để tạo job đầu tiên."/>}</section>;
  if(page==="review") return <section className="vam-panel"><h2>Clip chờ review <small>{pending.length}</small></h2>{pending.length?<div className="vam-review-grid">{pending.map(item=><article key={item.clip.id}><div className="vam-clip-cover"><Car/><span>{item.track?.vehicle_class??"vehicle"}</span></div><div><b>{item.filename??"Video"}</b><small>Track #{item.track?.track_id??"--"} · {item.clip.duration.toFixed(1)} giây</small><p>Confidence: {item.track?`${Math.round(item.track.avg_confidence*100)}%`:"--"}</p><footer><button onClick={()=>preview(item.clip)}><Eye/>Xem</button><button className="approve" onClick={()=>decide(item,"APPROVED")}><Check/>Duyệt</button><button className="reject" onClick={()=>decide(item,"REJECTED")}><X/>Loại</button></footer></div></article>)}</div>:<Empty icon={<CheckSquare/>} title="Không có clip chờ review" text="Các kết quả cần QC sẽ xuất hiện tại đây."/>}</section>;
  if(page==="alerts") return <section className="vam-panel"><h2>Cảnh báo</h2><Empty icon={<ShieldAlert/>} title="Chưa có dữ liệu SuspiciousEvent" text="Backend hiện mới lưu VehicleTrack và Clip. Module cảnh báo hành vi sẽ hiển thị khi SuspiciousEventService và API cảnh báo được triển khai."/></section>;
  if(page==="camera") return <section className="vam-panel"><h2>Nguồn camera</h2><Empty icon={<Camera/>} title="Chưa cấu hình camera" text="Thêm CameraRepository và CameraService trước khi kết nối RTSP/Camera Live. Frontend không kết nối trực tiếp camera hoặc database."/><button className="vam-primary" disabled>Thêm camera</button></section>;
  return <section className="vam-panel"><h2>Cấu hình phân tích</h2><div className="vam-settings"><label>Ngưỡng confidence<input value="0.50" readOnly/></label><label>Thời gian lảng vảng tối thiểu<input value="30 giây" readOnly/></label><label>Khoảng cách người - phương tiện<input value="120 px" readOnly/></label></div><p className="vam-note">Các giá trị đang ở chế độ chỉ đọc. Cần SettingsController → SettingsService → SettingsRepository trước khi cho phép lưu cấu hình.</p></section>;
}

function AnalysisPanel({preview}:{preview:(clip:Clip)=>void}) {
  const inputRef=useRef<HTMLInputElement>(null);
  const [file,setFile]=useState<File|null>(null);
  const [running,setRunning]=useState(false);
  const [progress,setProgress]=useState(0);
  const [message,setMessage]=useState("Chọn video giao thông để bắt đầu phân tích.");
  const [tracks,setTracks]=useState<VehicleTrack[]>([]);
  const [clips,setClips]=useState<Clip[]>([]);
  const run=async()=>{
    if(!file){setMessage("Hãy chọn một file video trước.");return;}
    try{
      setRunning(true);setProgress(0);setTracks([]);setClips([]);setMessage("Đang tải video lên hệ thống…");
      const video=await api.uploadVideo(file);
      const job=await api.startProcessing(video.id,{confidence_threshold:.5,vehicle_classes:["car","motorcycle","truck","bus"],padding_before:0,padding_after:0,min_clip_duration:1});
      setMessage("Worker đang phát hiện và theo dõi phương tiện.");
      const poll=async()=>{
        const current=await api.getJob(job.id);setProgress(current.progress);
        if(current.status==="COMPLETED"){
          const [foundTracks,generatedClips]=await Promise.all([api.getTracks(video.id),api.getClips(video.id)]);
          setTracks(foundTracks);setClips(generatedClips);setRunning(false);setMessage(`Xử lý thành công: ${foundTracks.length} phương tiện, ${generatedClips.length} clip.`);return;
        }
        if(current.status==="FAILED"){setRunning(false);setMessage(`Xử lý thất bại: ${current.error_message??"Không rõ nguyên nhân"}`);return;}
        window.setTimeout(()=>void poll(),1500);
      };
      window.setTimeout(()=>void poll(),800);
    }catch(reason){setRunning(false);setMessage(reason instanceof Error?reason.message:"Không thể gửi video xử lý");}
  };
  return <div className="vam-analysis"><section className="vam-panel vam-upload-panel"><div><h2>Video nguồn</h2><p>MP4, MOV hoặc AVI. File được lưu qua StorageService; metadata lưu ở PostgreSQL.</p></div><label className="vam-drop"><input ref={inputRef} type="file" accept="video/mp4,video/quicktime,video/x-msvideo" onChange={event=>setFile(event.target.files?.[0]??null)}/><Upload/><b>{file?file.name:"Chọn video để phân tích"}</b><small>{file?`${(file.size/1024/1024).toFixed(1)} MB`:"Kéo thả hoặc nhấn để chọn file"}</small></label><button className="vam-run" disabled={running} onClick={run}><Play/>{running?`Đang xử lý ${progress}%`:"Bắt đầu phân tích"}</button></section><section className="vam-panel vam-analysis-result"><div className="vam-result-head"><div><h2>Kết quả phát hiện</h2><p>{message}</p></div>{running&&<b>{progress}%</b>}</div>{tracks.length?<div className="vam-review-grid">{tracks.map(track=>{const clip=clips.find(item=>item.vehicle_track_id===track.id);return <article key={track.id}><div className="vam-clip-cover"><Car/><span>{track.vehicle_class}</span></div><div><b>Track #{track.track_id}</b><small>{track.start_time.toFixed(1)}s – {track.end_time.toFixed(1)}s</small><p>Confidence: {Math.round(track.avg_confidence*100)}% · {track.review_required?"Cần review":"Đạt"}</p>{clip&&<footer><button onClick={()=>preview(clip)}><Eye/>Xem clip</button></footer>}</div></article>})}</div>:<Empty icon={<Video/>} title={running?"Đang phân tích video":"Chưa có kết quả"} text={running?"Kết quả sẽ tự xuất hiện sau khi Celery worker hoàn tất.":"Phương tiện được YOLO phát hiện sẽ hiển thị tại đây."}/>}</section></div>;
}

function Kpi({icon,label,value}:{icon:React.ReactNode;label:string;value:number}){return <article className="vam-kpi"><span>{icon}</span><div><small>{label}</small><b>{value}</b></div></article>}
function Empty({icon,title,text}:{icon:React.ReactNode;title:string;text:string}){return <div className="vam-empty"><span>{icon}</span><b>{title}</b><p>{text}</p></div>}
