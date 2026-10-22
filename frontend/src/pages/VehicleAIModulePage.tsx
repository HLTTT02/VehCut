import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, Bell, Camera, Car, Check, CheckSquare, ChevronDown,
  Clock3, Eye, FileVideo, History, Home, RefreshCw, ScanLine, Settings,
  Play, ShieldAlert, Upload, Video, X, MapPin, Plus, Save, Trash2
} from "lucide-react";
import { api } from "../api/client";
import type { Clip, DetectionBox, JobHistory, RoiZone, Statistics, SuspiciousEvent, VehicleTrack, Video as VideoItem } from "../types/api";
import { VehicleAIOverview } from "./VehicleAIOverview";

export type ModulePage = "overview" | "analysis" | "roi" | "camera" | "alerts" | "review" | "history" | "statistics" | "settings";
type NavigatePage = ModulePage;
type ReviewItem = { clip: Clip; track?: VehicleTrack; filename?: string };

const emptyStats: Statistics = { total_videos:0,total_vehicles:0,total_clips:0,pending_review:0,completed_jobs:0,failed_jobs:0,vehicle_classes:{person:0,car:0,motorcycle:0,truck:0,bus:0} };
const pageMeta: Record<ModulePage,{title:string;description:string}> = {
  roi:{title:"Vùng ROI",description:"Vẽ khu vực giám sát và lọc đối tượng trước khi tracking."},
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
      <button className={page==="roi"?"active":""} onClick={()=>onNavigate("roi")}><MapPin/>Vùng ROI</button>
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
  if(page==="roi") return <RoiEditorPanel/>;
  if(page==="analysis") return <AnalysisPanel preview={preview}/>;
  if(page==="statistics") return <><div className="vam-kpi-row"><Kpi icon={<FileVideo/>} label="Video" value={statistics.total_videos}/><Kpi icon={<Car/>} label="Phương tiện" value={statistics.total_vehicles}/><Kpi icon={<Video/>} label="Clip" value={statistics.total_clips}/><Kpi icon={<ShieldAlert/>} label="Cần review" value={statistics.pending_review}/></div><section className="vam-panel"><h2>Phân bố phương tiện</h2><div className="vam-class-grid">{Object.entries(statistics.vehicle_classes).map(([name,value])=><div key={name}><span>{name}</span><b>{value}</b></div>)}</div></section></>;
  if(page==="history") return <section className="vam-panel"><h2>Job xử lý gần đây</h2>{history.length?<div className="vam-table"><div className="head"><span>Video</span><span>Trạng thái</span><span>Tiến độ</span><span>Hoàn tất</span></div>{history.map(job=><div key={job.id}><span><FileVideo/>{job.filename??job.video_id}</span><span className={`state ${job.status.toLowerCase()}`}>{job.status}</span><span>{job.progress}%</span><span>{job.completed_at?new Date(job.completed_at).toLocaleString("vi-VN"):"--"}</span></div>)}</div>:<Empty icon={<History/>} title="Chưa có lịch sử" text="Hãy phân tích một video để tạo job đầu tiên."/>}</section>;
  if(page==="review") return <section className="vam-panel"><h2>Clip chờ review <small>{pending.length}</small></h2>{pending.length?<div className="vam-review-grid">{pending.map(item=><article key={item.clip.id}><div className="vam-clip-cover"><Car/><span>{item.track?.vehicle_class??"vehicle"}</span></div><div><b>{item.filename??"Video"}</b><small>Track #{item.track?.track_id??"--"} · {item.clip.duration.toFixed(1)} giây</small><p>Confidence: {item.track?`${Math.round(item.track.avg_confidence*100)}%`:"--"}</p><footer><button onClick={()=>preview(item.clip)}><Eye/>Xem</button><button className="approve" onClick={()=>decide(item,"APPROVED")}><Check/>Duyệt</button><button className="reject" onClick={()=>decide(item,"REJECTED")}><X/>Loại</button></footer></div></article>)}</div>:<Empty icon={<CheckSquare/>} title="Không có clip chờ review" text="Các kết quả cần QC sẽ xuất hiện tại đây."/>}</section>;
  if(page==="alerts") return <AlertPanel/>;
  if(page==="camera") return <section className="vam-panel"><h2>Nguồn camera</h2><Empty icon={<Camera/>} title="Chưa cấu hình camera" text="Thêm CameraRepository và CameraService trước khi kết nối RTSP/Camera Live. Frontend không kết nối trực tiếp camera hoặc database."/><button className="vam-primary" disabled>Thêm camera</button></section>;
  return <section className="vam-panel"><h2>Cấu hình phân tích</h2><div className="vam-settings"><label>Ngưỡng confidence<input value="0.50" readOnly/></label><label>Thời gian lảng vảng tối thiểu<input value="30 giây" readOnly/></label><label>Khoảng cách người - phương tiện<input value="120 px" readOnly/></label></div><p className="vam-note">Các giá trị đang ở chế độ chỉ đọc. Cần SettingsController → SettingsService → SettingsRepository trước khi cho phép lưu cấu hình.</p></section>;
}

function AlertPanel(){
  const [alerts,setAlerts]=useState<SuspiciousEvent[]>([]);const [message,setMessage]=useState("Đang tải cảnh báo…");
  useEffect(()=>{void api.getAlerts().then(items=>{setAlerts(items);setMessage("");}).catch(()=>setMessage("Không thể tải cảnh báo."));},[]);
  return <section className="vam-panel vam-alert-panel"><h2>Cảnh báo không biển số</h2>{alerts.length?<div className="vam-alert-list">{alerts.map(alert=><article key={alert.id}><div className="vam-alert-image">{alert.screenshot_path?<img src={api.fileUrl(alert.screenshot_path)} alt="Phương tiện cảnh báo"/>:<ShieldAlert/>}</div><div><b>{alert.event_type==="NO_PLATE"?"Không phát hiện biển số":alert.event_type}</b><small>{new Date(alert.created_at).toLocaleString("vi-VN")} · {alert.severity}</small><p>{alert.message}</p><button onClick={()=>location.hash="analysis"}>Xem video phân tích</button></div></article>)}</div>:<Empty icon={<ShieldAlert/>} title="Chưa có cảnh báo" text={message||"Xe không có biển số hoặc OCR không đọc được sẽ xuất hiện tại đây kèm ảnh phương tiện."}/>}</section>;
}

function AnalysisPanel({preview}:{preview:(clip:Clip)=>void}) {
  const inputRef=useRef<HTMLInputElement>(null);
  const [file,setFile]=useState<File|null>(null);
  const [videos,setVideos]=useState<VideoItem[]>([]);
  const [selectedVideoId,setSelectedVideoId]=useState("");
  const [zones,setZones]=useState<RoiZone[]>([]);
  const [localPreview,setLocalPreview]=useState<string|null>(null);
  const [boxes,setBoxes]=useState<DetectionBox[]>([]);
  const [visibleClasses,setVisibleClasses]=useState<Record<"person"|"motorcycle"|"car",boolean>>({person:true,motorcycle:true,car:true});
  const lastDetectionTime=useRef(-1);
  const [running,setRunning]=useState(false);
  const [progress,setProgress]=useState(0);
  const [message,setMessage]=useState("Chọn video giao thông để bắt đầu phân tích.");
  const [tracks,setTracks]=useState<VehicleTrack[]>([]);
  const [clips,setClips]=useState<Clip[]>([]);
  const selectedVideo=videos.find(video=>video.id===selectedVideoId);
  useEffect(()=>{void api.getVideos().then(setVideos).catch(()=>undefined);},[]);
  useEffect(()=>{if(!selectedVideoId){setZones([]);return;}void api.getRoiZones(selectedVideoId).then(setZones).catch(()=>setZones([]));},[selectedVideoId]);
  useEffect(()=>{if(!file){setLocalPreview(null);return;}const url=URL.createObjectURL(file);setLocalPreview(url);return()=>URL.revokeObjectURL(url);},[file]);
  const loadBoxes=async(timeSeconds:number)=>{
    if(!selectedVideoId)return;
    try{setBoxes((await api.getFrameDetections(selectedVideoId,timeSeconds)).detections);}
    catch{setBoxes([]);}
  };
  useEffect(()=>{if(selectedVideoId)void loadBoxes(0);},[selectedVideoId]);
  const onVideoTime=(event:React.SyntheticEvent<HTMLVideoElement>)=>{
    const time=event.currentTarget.currentTime;
    if(Math.abs(time-lastDetectionTime.current)<0.5)return;
    lastDetectionTime.current=time;void loadBoxes(time);
  };
  const run=async()=>{
    if(!file&&!selectedVideo){setMessage("Hãy chọn video mới hoặc video đã tải lên.");return;}
    try{
      setRunning(true);setProgress(0);setTracks([]);setClips([]);setMessage("Đang tải video lên hệ thống…");
      const uploaded=file?await api.uploadVideo(file):null;
      const video=uploaded?await api.getVideo(uploaded.id):selectedVideo!;
      if(file){setVideos(items=>[video,...items.filter(item=>item.id!==video.id)]);setSelectedVideoId(video.id);setZones(await api.getRoiZones(video.id));}
      await loadBoxes(0);
      const job=await api.startProcessing(video.id,{confidence_threshold:.5,vehicle_classes:["person","car","motorcycle","truck","bus"],padding_before:0,padding_after:0,min_clip_duration:1});
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
  const isImage = file?.type.startsWith("image/");
  const sourceUrl=localPreview??(selectedVideo?api.fileUrl(selectedVideo.original_path):null);
  const points=(items:RoiZone["points"])=>items.map(point=>`${point.x*100},${point.y*100}`).join(" ");
  const displayedBoxes=boxes.filter(box=>box.vehicle_class in visibleClasses?visibleClasses[box.vehicle_class as keyof typeof visibleClasses]:true);
  const toggleClass=(value:keyof typeof visibleClasses)=>setVisibleClasses(current=>({...current,[value]:!current[value]}));
  const hasEnabledRoi=zones.some(zone=>zone.enabled);
  return <div className="vam-analysis"><section className="vam-panel vam-upload-panel"><div><h2>Ảnh hoặc video nguồn</h2><p>Chọn video đã tải để áp dụng ROI đã lưu, hoặc tải file mới.</p></div><select className="vam-video-select" value={selectedVideoId} onChange={event=>{setFile(null);setBoxes([]);setSelectedVideoId(event.target.value);}}><option value="">Chọn video đã tải</option>{videos.map(video=><option key={video.id} value={video.id}>{video.filename}</option>)}</select><label className="vam-drop"><input ref={inputRef} type="file" accept="video/mp4,video/quicktime,video/x-msvideo,image/jpeg,image/png,image/webp" onChange={event=>{setSelectedVideoId("");setBoxes([]);setFile(event.target.files?.[0]??null);}}/><Upload/><b>{file?file.name:"Hoặc chọn ảnh/video mới"}</b><small>{file?`${(file.size/1024/1024).toFixed(1)} MB · ${isImage?"Image detection":"Video detection + tracking"}`:"Kéo thả hoặc nhấn để chọn file"}</small></label><button className="vam-run" disabled={running||!!selectedVideoId&&!hasEnabledRoi} onClick={run}><Play/>{running?`Đang xử lý ${progress}%`:"Bắt đầu phân tích"}</button>{selectedVideoId&&!hasEnabledRoi&&<p className="vam-analysis-hint">Video này chưa có ROI đang bật. Hãy vẽ/bật ROI trước khi phân tích sự kiện.</p>}</section><section className="vam-panel vam-analysis-result"><div className="vam-result-head"><div><h2>Video và vùng ROI</h2><p>{sourceUrl?`${zones.filter(zone=>zone.enabled).length} vùng ROI đang bật · ${displayedBoxes.length} đối tượng trong vùng. ${message}`:message}</p></div>{running&&<b>{progress}%</b>}</div><div className="vam-detection-toggles">{([['person','Người'],['motorcycle','Xe máy'],['car','Ô tô']] as const).map(([value,label])=><button key={value} className={visibleClasses[value]?`on ${value}`:""} onClick={()=>toggleClass(value)}><i/>{label}<span>{visibleClasses[value]?"Đang hiện":"Đang ẩn"}</span></button>)}</div>{sourceUrl?<div className="vam-analysis-preview"><video controls src={sourceUrl} onTimeUpdate={onVideoTime} onSeeked={onVideoTime}/><svg viewBox="0 0 100 100" preserveAspectRatio="none">{zones.filter(zone=>zone.enabled).map(zone=><polygon key={zone.id} points={points(zone.points)} className="vam-analysis-roi"/>)}{zones.filter(zone=>zone.enabled).map(zone=>{const first=zone.points[0];return first?<text key={`${zone.id}-label`} x={first.x*100} y={Math.max(4,first.y*100-2)}>{zone.name}</text>:null;})}{displayedBoxes.map((box,index)=><g key={`${box.vehicle_class}-${index}`} className={`vam-detection vam-${box.vehicle_class}`}><rect x={box.x1*100} y={box.y1*100} width={(box.x2-box.x1)*100} height={(box.y2-box.y1)*100}/><text x={box.x1*100} y={Math.max(4,box.y1*100-2)}>{box.vehicle_class} {(box.confidence*100).toFixed(0)}%</text></g>)}</svg></div>:<Empty icon={<Video/>} title="Chưa chọn video" text="Chọn video đã tải để xem vùng ROI, hoặc tải file mới."/>}{tracks.length?<div className="vam-review-grid">{tracks.map(track=>{const clip=clips.find(item=>item.vehicle_track_id===track.id);return <article key={track.id}><div className="vam-clip-cover"><Car/><span>{track.vehicle_class}</span></div><div><b>{isImage?"Detection":"Track"} #{track.track_id}</b><small>{isImage?"Ảnh tĩnh":`${track.start_time.toFixed(1)}s – ${track.end_time.toFixed(1)}s`}</small><p>Confidence: {Math.round(track.avg_confidence*100)}% · {track.review_required?"Cần review":"Đạt"}</p>{clip&&<footer><button onClick={()=>preview(clip)}><Eye/>Xem clip</button></footer>}</div></article>})}</div>:running?null:<div className="vam-analysis-hint">Khung chỉ xuất hiện khi đối tượng đi vào ROI đang bật; ngoài ROI không có detect/event.</div>}</section></div>;
}

function RoiEditorPanel() {
  const [videos,setVideos]=useState<import("../types/api").Video[]>([]);
  const [videoId,setVideoId]=useState("");
  const [zones,setZones]=useState<import("../types/api").RoiZone[]>([]);
  const [draft,setDraft]=useState<import("../types/api").RoiPoint[]>([]);
  const [name,setName]=useState("Vùng giám sát");
  const [message,setMessage]=useState("Chọn video rồi click ít nhất 3 điểm để vẽ vùng ROI.");
  const surfaceRef=useRef<HTMLDivElement>(null);
  const video=videos.find(item=>item.id===videoId);
  useEffect(()=>{let active=true;void api.getVideos().then(async items=>{const zoneLists=await Promise.all(items.map(item=>api.getRoiZones(item.id).catch(()=>[])));if(!active)return;setVideos(items);const firstWithRoi=zoneLists.findIndex(zones=>zones.length>0);setVideoId(items[firstWithRoi>=0?firstWithRoi:0]?.id??"");}).catch(()=>setMessage("Không thể tải danh sách video."));return()=>{active=false};},[]);
  useEffect(()=>{if(!videoId){setZones([]);return;} void api.getRoiZones(videoId).then(setZones).catch(()=>setMessage("Không thể tải các vùng ROI."));setDraft([]);},[videoId]);
  const addPoint=(event:React.MouseEvent<HTMLDivElement>)=>{const element=surfaceRef.current;if(!element)return;const rect=element.getBoundingClientRect();setDraft(points=>[...points,{x:Number(((event.clientX-rect.left)/rect.width).toFixed(4)),y:Number(((event.clientY-rect.top)/rect.height).toFixed(4))}]);};
  const save=async()=>{if(!videoId||draft.length<3){setMessage("ROI cần ít nhất 3 điểm.");return;}try{const zone=await api.createRoiZone(videoId,{name:name.trim()||"Vùng giám sát",points:draft,enabled:true});setZones(items=>[...items,zone]);setDraft([]);setMessage("Đã lưu ROI. Lần xử lý tiếp theo sẽ chỉ nhận bbox trong vùng này.");}catch(reason){setMessage(reason instanceof Error?reason.message:"Không thể lưu ROI.");}};
  const remove=async(id:string)=>{try{await api.deleteRoiZone(id);setZones(items=>items.filter(item=>item.id!==id));}catch{setMessage("Không thể xóa ROI.");}};
  const toggle=async(zone:import("../types/api").RoiZone)=>{try{const updated=await api.updateRoiZone(zone.id,{enabled:!zone.enabled});setZones(items=>items.map(item=>item.id===zone.id?updated:item));}catch{setMessage("Không thể cập nhật ROI.");}};
  const pointText=(points:import("../types/api").RoiPoint[])=>points.map(point=>`${point.x*100},${point.y*100}`).join(" ");
  return <div className="vam-roi"><section className="vam-panel"><header className="vam-roi-head"><div><h2>Vẽ vùng giám sát</h2><p>{message}</p></div><select value={videoId} onChange={event=>setVideoId(event.target.value)}><option value="">Chọn video đã tải</option>{videos.map(item=><option key={item.id} value={item.id}>{item.filename}</option>)}</select></header>{video?<div ref={surfaceRef} className="vam-roi-canvas" onClick={addPoint}><video muted controls src={api.fileUrl(video.original_path)}/><svg viewBox="0 0 100 100" preserveAspectRatio="none">{zones.filter(zone=>zone.enabled).map(zone=><polygon key={zone.id} points={pointText(zone.points)} className="saved"/>)}{draft.length>0&&<><polyline points={pointText(draft)} className="draft"/>{draft.map((point,index)=><circle key={index} cx={point.x*100} cy={point.y*100} r="1.2" className="point"/>)}</>}</svg></div>:<Empty icon={<MapPin/>} title="Chưa có video" text="Hãy tải video ở trang Phân tích video trước khi tạo ROI."/>}<footer className="vam-roi-actions"><input value={name} maxLength={100} onChange={event=>setName(event.target.value)} placeholder="Tên vùng ROI"/><button onClick={()=>setDraft([])}>Xóa điểm đang vẽ</button><button className="vam-primary" disabled={!videoId||draft.length<3} onClick={()=>void save()}><Save/>Lưu ROI ({draft.length} điểm)</button></footer></section><section className="vam-panel"><h2>ROI đã lưu</h2>{zones.length?<div className="vam-roi-list">{zones.map(zone=><article key={zone.id}><span><MapPin/></span><div><b>{zone.name}</b><small>{zone.points.length} điểm · {zone.enabled?"Đang áp dụng":"Tạm tắt"}</small></div><button onClick={()=>void toggle(zone)}>{zone.enabled?"Tắt":"Bật"}</button><button className="danger" onClick={()=>void remove(zone.id)} aria-label="Xóa ROI"><Trash2/></button></article>)}</div>:<Empty icon={<Plus/>} title="Chưa có vùng ROI" text="Các vùng đã lưu sẽ áp dụng trong lần xử lý video tiếp theo."/>}</section></div>;
}

function Kpi({icon,label,value}:{icon:React.ReactNode;label:string;value:number}){return <article className="vam-kpi"><span>{icon}</span><div><small>{label}</small><b>{value}</b></div></article>}
function Empty({icon,title,text}:{icon:React.ReactNode;title:string;text:string}){return <div className="vam-empty"><span>{icon}</span><b>{title}</b><p>{text}</p></div>}
