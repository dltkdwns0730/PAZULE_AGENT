import { useState, useEffect } from "react";
import "./App.css";
import logoImage from "./assets/로고사진.png";
import intro1 from "./assets/인트로1.jpg";
import intro2 from "./assets/인트로2.jpg";
import intro3 from "./assets/인트로3.jpg";
import intro4 from "./assets/인트로4.jpg";
import intro5 from "./assets/인트로5.jpg";
import intro6 from "./assets/인트로6.jpg";
import intro7 from "./assets/인트로7.jpg";
import intro8 from "./assets/인트로8.jpg";

function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [step, setStep] = useState("intro"); // "intro", "select", "upload", "result"
  const [currentIntroImage, setCurrentIntroImage] = useState(0);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [missionType, setMissionType] = useState("photo");
  const [status, setStatus] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [todayHint, setTodayHint] = useState("");
  const [hintLoading, setHintLoading] = useState(true);
  const [history, setHistory] = useState([]);
  const [completedMissions, setCompletedMissions] = useState({
    photo: false,
    location: false
  });

  const API_ENDPOINT = "http://localhost:8080";

  const introImages = [intro1, intro2, intro3, intro4, intro5, intro6, intro7, intro8];

  // 히스토리에 쿠폰 저장
  const saveToHistory = (resultData) => {
    if (resultData.success && resultData.coupon) {
      const historyItem = {
        id: Date.now(),
        date: new Date().toISOString(),
        missionType: resultData.missionType || missionType,
        coupon: resultData.coupon.code || resultData.coupon,
        couponDescription: resultData.coupon.description || "",
        success: true
      };
      setHistory((prevHistory) => {
        return [historyItem, ...prevHistory];
      });

      const completedType = resultData.missionType || missionType;
      if (completedType) {
        setCompletedMissions((prev) => {
          if (prev[completedType]) {
            return prev;
          }
          return {
            ...prev,
            [completedType]: true
          };
        });
      }
    }
  };

  // 인트로 이미지 슬라이드쇼
  useEffect(() => {
    if (step === "intro") {
      const interval = setInterval(() => {
        setCurrentIntroImage((prev) => (prev + 1) % introImages.length);
      }, 4000); // 4초마다 변경
      return () => clearInterval(interval);
    }
  }, [step, introImages.length]);

  const missionTypes = [
    { 
      value: "photo", 
      label: "감성 촬영", 
      description: "감정이 담긴 사진을 찍어 업로드하세요",
      icon: "📷"
    },
    { 
      value: "location", 
      label: "장소 촬영", 
      description: "구조물이 있는 장소를 찾아가세요",
      icon: "📍"
    },
  ];

  // ✅ 서버에서 오늘의 힌트 가져오기 (mission_type에 따라)
  useEffect(() => {
    // upload 단계일 때만 힌트 가져오기
    if (step === "upload") {
      const fetchTodayHint = async () => {
        try {
          setHintLoading(true);
          // mission_type에 따라 다른 힌트 가져오기
          // "photo" -> missions2, "location" -> missions1
          const missionParam = missionType === "photo" ? "photo" : "location";
          const response = await fetch(`${API_ENDPOINT}/get-today-hint?mission_type=${missionParam}`);
          if (response.ok) {
            const data = await response.json();
            setTodayHint(data.hint || "");
          } else {
            console.error("힌트 가져오기 실패");
            setTodayHint("힌트를 불러올 수 없습니다.");
          }
        } catch (err) {
          console.error("힌트 가져오기 오류:", err);
          setTodayHint("힌트를 불러올 수 없습니다.");
        } finally {
          setHintLoading(false);
        }
      };

      fetchTodayHint();
    }
  }, [missionType, step]); // missionType과 step이 변경될 때마다 힌트 다시 가져오기

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setResult(null);
    
    // HEIC 파일 감지 (확장자 확인)
    const fileName = file.name.toLowerCase();
    const isHeic = fileName.endsWith('.heic') || fileName.endsWith('.heif');
    
    // 파일을 state에 저장 (서버로 전송할 파일)
    setImage(file);
    
    // HEIC/HEIF 파일인 경우 서버에서 변환된 미리보기 가져오기
    if (isHeic) {
      try {
        console.log('HEIC/HEIF 파일 감지, 서버에서 미리보기 변환 중...');
        
        // 서버로 HEIC 파일 전송하여 JPG로 변환된 미리보기 받기
        const formData = new FormData();
        formData.append("image", file);
        
        const response = await fetch(`${API_ENDPOINT}/api/preview`, {
          method: "POST",
          body: formData,
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const reader = new FileReader();
          reader.onload = () => setPreview(reader.result);
          reader.readAsDataURL(blob);
          console.log('HEIC/HEIF → JPG 미리보기 변환 완료');
        } else {
          throw new Error('서버 변환 실패');
        }
      } catch (error) {
        console.error('HEIC 미리보기 변환 실패:', error);
        // 변환 실패 시 기본 이미지 아이콘 표시
        setPreview(null);
        // 파일은 그대로 유지 (서버에서 처리 가능)
      }
    } else {
      // 일반 이미지 파일 (JPEG, PNG 등) - 직접 미리보기
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async () => {
    if (completedMissions[missionType]) {
      alert("이미 성공한 미션입니다. 다른 미션을 선택해주세요.");
      setStep("select");
      setActiveTab("home");
      return;
    }
    if (!image) {
      alert("이미지를 선택해주세요.");
      return;
    }
    if (!missionType) {
      alert("미션 타입을 선택해주세요.");
      return;
    }

    setLoading(true);
    setStatus("미션 진행 중...");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("image", image);
      formData.append("mission_type", missionType);

      const response = await fetch(`${API_ENDPOINT}/api/mission`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        // 서버에서 반환한 에러 메시지 사용
        throw new Error(data.error || `서버 오류: ${response.status}`);
      }

      setStatus("완료!");
      setResult(data);
      // 성공한 경우 히스토리에 저장
      if (data.success) {
        saveToHistory(data);
      }
      setStep("result"); // 결과 화면으로 이동
    } catch (err) {
      // 서버에서 반환한 에러 메시지를 그대로 표시
      setStatus(err.message);
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setPreview(null);
    setMissionType("photo");
    setStatus("");
    setResult(null);
    setLoading(false);
    setStep("select"); // 처음 화면으로 돌아가기
    setActiveTab("home");
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) fileInput.value = "";
  };

  // 미션 타입 선택 시 업로드 화면으로 이동
  const handleMissionTypeSelect = (type) => {
    if (completedMissions[type]) {
      alert("이미 성공한 미션입니다. 다른 미션을 선택해주세요.");
      return;
    }
    setMissionType(type);
    setStep("upload");
    // 미션 타입에 맞는 탭으로 이동
    if (type === "photo") {
      setActiveTab("photo");
    } else if (type === "location") {
      setActiveTab("location");
    }
  };

  // 뒤로 가기 버튼
  const handleBack = () => {
    if (step === "upload") {
      setStep("select");
      setActiveTab("home");
      setImage(null);
      setPreview(null);
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = "";
    } else if (step === "result") {
      setStep("upload");
      setResult(null);
      setStatus("");
    }
  };

  // 트로피 아이콘 SVG
  const TrophyIcon = () => (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 9H4C2.89543 9 2 9.89543 2 11V13C2 14.1046 2.89543 15 4 15H6M18 9H20C21.1046 9 22 9.89543 22 11V13C22 14.1046 21.1046 15 20 15H18M6 15V19C6 20.1046 6.89543 21 8 21H16C17.1046 21 18 20.1046 18 19V15M6 15H18M12 5V2M12 2L9 5M12 2L15 5M12 5C9.79086 5 8 6.79086 8 9V11C8 12.1046 8.89543 13 10 13H14C15.1046 13 16 12.1046 16 11V9C16 6.79086 14.2091 5 12 5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  // 별 아이콘 SVG
  const StarIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
    </svg>
  );

  // 전구 아이콘 SVG
  const BulbIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 21H15M12 3C8.68629 3 6 5.68629 6 9C6 11.0929 7.20207 12.8945 9 13.8681V17C9 17.5523 9.44772 18 10 18H14C14.5523 18 15 17.5523 15 17V13.8681C16.7979 12.8945 18 11.0929 18 9C18 5.68629 15.3137 3 12 3Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  // 뒤로가기 아이콘 SVG
  const BackIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  // 별 아이콘 SVG (인트로용)
  const SparkleIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L13.5 8.5L20 10L13.5 11.5L12 18L10.5 11.5L4 10L10.5 8.5L12 2Z"/>
    </svg>
  );

  // 나뭇잎 아이콘 SVG
  const LeafIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 21C3 21 5 13 11 7C17 1 21 3 21 3C21 3 23 7 17 13C11 19 3 21 3 21Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 21C3 21 9 17 13 13C17 9 21 3 21 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  // 지도 핀 아이콘 SVG
  const MapPinIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M21 10C21 17 12 23 12 23C12 23 3 17 3 10C3 7.61305 3.94821 5.32387 5.63604 3.63604C7.32387 1.94821 9.61305 1 12 1C14.3869 1 16.6761 1.94821 18.364 3.63604C20.0518 5.32387 21 7.61305 21 10Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 13C13.6569 13 15 11.6569 15 10C15 8.34315 13.6569 7 12 7C10.3431 7 9 8.34315 9 10C9 11.6569 10.3431 13 12 13Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  // 화살표 아이콘 SVG
  const ArrowRightIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  return (
    <div className="app-container">
      {step === "intro" ? (
        <div className="intro-page">
          {/* 배경 이미지 슬라이드쇼 */}
          <div className="intro-background">
            {introImages.map((img, index) => (
              <img
                key={index}
                src={img}
                alt={`인트로 ${index + 1}`}
                className={`intro-bg-image ${index === currentIntroImage ? "active" : ""}`}
              />
            ))}
            <div className="intro-overlay"></div>
          </div>

          {/* 콘텐츠 */}
          <div className="intro-content">
            {/* 로고 */}
            <div className="intro-logo-container">
              <img src={logoImage} alt="PAZULE" className="intro-logo" />
            </div>

            {/* 메인 타이틀 */}
            <h1 className="intro-main-title">미션을 완료하고 특별한 쿠폰을 받아가세요 !</h1>

            {/* 시작하기 버튼 */}
            <button className="intro-start-btn" onClick={() => {
              setStep("select");
              setActiveTab("home");
            }}>
              <span>시작하기</span>
              <ArrowRightIcon />
            </button>

            {/* 푸터 텍스트 */}
            <p className="intro-footer">파주의 아름다움을 발견하는 특별한 여행</p>
          </div>
        </div>
      ) : step === "result" && result ? (
        <div className="result-page-wrapper">
          <div className="result-page">
            {/* 큰 이미지 섹션 */}
            <div className="result-image-section">
              {preview && (
                <img src={preview} alt="업로드한 이미지" className="result-main-image" />
              )}
            </div>
            
            {/* 결과 정보 카드 */}
            <div className={`result-info-card ${result.success ? "success" : "fail"}`}>
              {result.success ? (
                <>
                  <div className="result-header">
                    <div className="result-title-section">
                      <h2 className="result-title">🎉 미션 성공!</h2>
                      <div className="result-badge success-badge">성공</div>
                    </div>
                  </div>
                  
                  <div className="result-content">
                    <div className="coupon-section">
                      <h3 className="section-title">쿠폰 지급</h3>
                      <div className="coupon-box">
                        {result.coupon ? (
                          <div>
                            <p className="coupon-code">{result.coupon.code || result.coupon}</p>
                            {result.coupon.description && (
                              <p className="coupon-description">{result.coupon.description}</p>
                            )}
                          </div>
                        ) : (
                          <p className="coupon-message">쿠폰이 지급되었습니다!</p>
                        )}
                      </div>
                    </div>
                    {result.message && (
                      <p className="result-message">{result.message}</p>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="result-header">
                    <div className="result-title-section">
                      <h2 className="result-title">😔 미션 실패</h2>
                      <div className="result-badge fail-badge">실패</div>
                    </div>
                  </div>
                  
                  <div className="result-content">
                    <div className="hint-section-result">
                      <h3 className="section-title">힌트</h3>
                      <div className="hint-box">
                        <p>{result.hint || "다시 시도해보세요!"}</p>
                      </div>
                    </div>
                    {result.message && (
                      <p className="result-message">{result.message}</p>
                    )}
                  </div>
                </>
              )}
              
              <button className="reset-btn" onClick={handleReset}>
                다시 시작하기
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="mission-container">
          {/* 헤더 */}
          {step !== "select" && (
            <div className="header">
              <button className="back-btn" onClick={handleBack}>
                <BackIcon />
              </button>
              <div className="logo-container">
                <img src={logoImage} alt="PAZULE" className="logo" />
              </div>
              <h1 className="title">오늘의 미션</h1>
              <p className="subtitle">키워드를 찾아 미션을 완료하고 쿠폰을 받으세요!</p>
            </div>
          )}

          {/* Select 단계에서만 로고 표시 */}
          {step === "select" && (
            <div className="select-header">
              <div className="select-header-top">
                <div className="logo-container-clickable" onClick={() => setStep("intro")}>
                  <img src={logoImage} alt="PAZULE" className="select-logo" />
                </div>
                <div className="header-divider"></div>
              </div>
            </div>
          )}

        {activeTab === "home" && (
          <>
            {/* 홈 화면 - 미션 선택 */}
            {step === "select" && (
              <>
                {/* 환영 헤더 */}
                <div className="welcome-header">
                  <h2 className="welcome-title">미션 완료 혜택</h2>
                  <p className="welcome-subtitle">미션을 성공하면 파주의 특별한 장소에서 사용할 수 있는 쿠폰을 받을 수 있어요!</p>
                  <div className="completion-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <span>완료 {history.filter(h => h.success).length}개</span>
                  </div>
                </div>

                {/* 오늘의 미션 섹션 */}
                <div className="mission-type-section">
                  <h3 className="section-heading">오늘의 미션</h3>
                  <div className="mission-type-cards">
                    {missionTypes.map((type) => {
                      const isCompleted = completedMissions[type.value];
                      return (
                        <div
                          key={type.value}
                          className={`mission-card-new ${isCompleted ? "completed" : ""}`}
                          onClick={() => {
                            if (!isCompleted) {
                              handleMissionTypeSelect(type.value);
                            }
                          }}
                        >
                          <div className="mission-card-icon-wrapper">
                            {type.value === "photo" ? (
                              <LeafIcon />
                            ) : (
                              <MapPinIcon />
                            )}
                          </div>
                          <div className="mission-card-content">
                            <h4 className="mission-card-title">{type.label}</h4>
                            <p className="mission-card-description">{type.description}</p>
                            <button className="mission-card-start-btn" disabled={isCompleted}>
                              {isCompleted ? "완료됨" : "시작하기 →"}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* 이미지 업로드 화면 - 감성 촬영/장소 촬영 탭에서 표시 */}
        {(activeTab === "photo" || activeTab === "location") && (
          <>
            {/* Step 2: 이미지 업로드 화면 */}
            {step === "upload" && (
              <>
                {/* 오늘의 힌트 */}
                <div className="keyword-section">
                  <div className="hint-section">
                    <BulbIcon />
                    <span className="hint-label">오늘의 힌트</span>
                  </div>
                  <p className="hint-text">
                    {hintLoading ? "힌트를 불러오는 중..." : todayHint || "힌트를 불러올 수 없습니다."}
                  </p>
                </div>

                {/* 이미지 업로드 */}
                <div className="upload-section">
                  <label className="label">이미지 업로드</label>
                  {preview ? (
                    <div className="image-preview-container">
                      <img src={preview} alt="미리보기" className="preview-image" />
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="file-input"
                        id="image-upload"
                        disabled={loading}
                      />
                      <label htmlFor="image-upload" className="change-image-btn">
                        다른 이미지 선택
                      </label>
                    </div>
                  ) : (
                    <div className="upload-area">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="file-input"
                        id="image-upload"
                        disabled={loading}
                      />
                      <label htmlFor="image-upload" className="file-input-label">
                        이미지 선택
                      </label>
                    </div>
                  )}
                </div>

                {/* 미션 제출 버튼 */}
                <button
                  className="submit-btn"
                  onClick={handleSubmit}
                  disabled={!image || !missionType || loading || completedMissions[missionType]}
                >
                  {loading ? "처리 중..." : "미션 제출하기"}
                </button>

                {/* 상태 메시지 */}
                {status && !result && (
                  <div className={`status-message ${loading ? "loading" : ""}`}>
                    {status}
                  </div>
                )}
              </>
            )}

          </>
        )}

        {/* 히스토리 화면 */}
        {activeTab === "history" && step === "select" && (
            <div className="history-section">
              <div className="history-header">
                <img src={logoImage} alt="PAZULE" className="history-logo" />
                <h2 className="history-title">쿠폰 히스토리</h2>
              </div>
              {history.length === 0 ? (
                <div className="history-empty">
                  <p>아직 받은 쿠폰이 없습니다.</p>
                  <p className="history-empty-sub">미션을 완료하고 쿠폰을 받아보세요!</p>
                </div>
              ) : (
                <div className="history-list">
                  {history.map((item) => (
                    <div key={item.id} className="history-item">
                      <div className="history-item-header">
                        <div className="history-item-type">
                          {item.missionType === "photo" ? "📷 감성 촬영" : "📍 장소 촬영"}
                        </div>
                        <div className="history-item-date">
                          {new Date(item.date).toLocaleDateString("ko-KR", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit"
                          })}
                        </div>
                      </div>
                      <div className="history-item-coupon">
                        <div className="coupon-label">쿠폰 코드</div>
                        <div className="coupon-code-display">{item.coupon}</div>
                        {item.couponDescription && (
                          <div className="coupon-description-display">{item.couponDescription}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 하단 네비게이션 바 */}
      {step !== "result" && step !== "intro" && (
        <div className="bottom-navigation">
          <button
            className={`nav-btn ${activeTab === "home" ? "active" : ""}`}
            onClick={() => {
              setStep("select");
              setActiveTab("home");
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M9 22V12H15V22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>홈</span>
          </button>
          <button
            className={`nav-btn ${activeTab === "photo" ? "active" : ""}`}
            onClick={() => {
              if (completedMissions.photo) {
                alert("이미 성공한 미션입니다. 다른 미션을 선택해주세요.");
                return;
              }
              setMissionType("photo");
              setStep("upload");
              setActiveTab("photo");
            }}
          >
            <LeafIcon />
            <span>감성 촬영</span>
          </button>
          <button
            className={`nav-btn ${activeTab === "location" ? "active" : ""}`}
            onClick={() => {
              if (completedMissions.location) {
                alert("이미 성공한 미션입니다. 다른 미션을 선택해주세요.");
                return;
              }
              setMissionType("location");
              setStep("upload");
              setActiveTab("location");
            }}
          >
            <MapPinIcon />
            <span>장소 촬영</span>
          </button>
          <button
            className={`nav-btn ${activeTab === "history" ? "active" : ""}`}
            onClick={() => {
              setStep("select");
              setActiveTab("history");
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 3H21L20 21H4L3 3Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 12L10 14L16 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>히스토리</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
