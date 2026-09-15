import json, glob, os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from backend.services.player_search import people as PEOPLE_DF, alias_map, full_name_map

FORMAT_FOLDERS={"test":"backend/data/matches/test","odi":"backend/data/matches/odi","t20i":"backend/data/matches/t20i"}
OUT="frontend/data"
NON_BOWLER={"run out","retired hurt","retired out","obstructing the field","timed out","retired not out"}
FEATURES=["batting_average","strike_rate","runs_per_innings","fours_per_innings","sixes_per_innings","fifties_per_innings","hundreds_per_innings","highest_score","wickets_per_match","bowling_average","economy","catches_per_match","run_outs_per_match","stumpings_per_match","matches"]
WEIGHTS=[1.5,1.2,1.4,1,1,1,1.2,.8,1.2,1,1,.7,.5,.5,.5]

def display_name(pid):
    if pid in full_name_map: return str(full_name_map[pid]).title()
    r=PEOPLE_DF[PEOPLE_DF.identifier.astype(str)==str(pid)]
    if r.empty:return str(pid)
    return str(r.iloc[0].get("unique_name") or r.iloc[0].get("name") or pid).title()

def player_index():
    out=[]
    for _,r in PEOPLE_DF.iterrows():
        pid=str(r.identifier)
        out.append({"id":pid,"name":display_name(pid),"registered_name":str(r.get("name","")).strip(),"unique_name":str(r.get("unique_name","")).strip(),"aliases":alias_map.get(pid,[])})
    out.sort(key=lambda x:x["name"].lower()); return out

def blank(pid,name):
    return {"player_id":pid,"name":name,"matches":0,"batting_innings":0,"runs":0,"balls_faced":0,"fours":0,"sixes":0,"dismissals":0,"fifties":0,"hundreds":0,"highest_score":0,"highest_score_not_out":False,"bowling_innings":0,"bowling_balls":0,"runs_conceded":0,"wickets":0,"four_wicket_hauls":0,"five_wicket_hauls":0,"best_bowling_wickets":0,"best_bowling_runs":None,"catches":0,"run_outs":0,"stumpings":0}

def aggregate(fmt):
    files=glob.glob(os.path.join(FORMAT_FOLDERS[fmt],"*.json"))
    if not files: raise FileNotFoundError(FORMAT_FOLDERS[fmt])
    ps={}
    for n,path in enumerate(files,1):
        with open(path,encoding="utf-8") as f:m=json.load(f)
        people=m.get("info",{}).get("registry",{}).get("people",{})
        for name,pid in people.items():
            ps.setdefault(pid,blank(pid,name))["matches"]+=1
        for inn in m.get("innings",[]):
            bat,bowl,outs={},{},set()
            for over in inn.get("overs",[]):
                for d in over.get("deliveries",[]):
                    batter,bowler=d.get("batter"),d.get("bowler"); rd=d.get("runs",{}); ex=d.get("extras",{})
                    br=rd.get("batter",0); tr=rd.get("total",0)
                    if batter in people:
                        pid=people[batter]; x=bat.setdefault(pid,{"runs":0,"balls":0,"fours":0,"sixes":0}); x["runs"]+=br
                        if "wides" not in ex:x["balls"]+=1
                        if br==4 and not rd.get("non_boundary",False):x["fours"]+=1
                        if br==6 and not rd.get("non_boundary",False):x["sixes"]+=1
                    if bowler in people:
                        pid=people[bowler]; x=bowl.setdefault(pid,{"balls":0,"runs":0,"wickets":0})
                        if "wides" not in ex and "noballs" not in ex:x["balls"]+=1
                        x["runs"]+=tr-ex.get("byes",0)-ex.get("legbyes",0)-ex.get("penalty",0)
                    for w in d.get("wickets",[]):
                        kind=w.get("kind","").lower(); po=w.get("player_out")
                        if po in people:outs.add(people[po])
                        if bowler in people and kind not in NON_BOWLER:
                            bowl.setdefault(people[bowler],{"balls":0,"runs":0,"wickets":0})["wickets"]+=1
                        for f in w.get("fielders",[]):
                            fn=f.get("name")
                            if fn not in people:continue
                            fp=ps[people[fn]]
                            if kind=="caught":fp["catches"]+=1
                            elif kind=="run out":fp["run_outs"]+=1
                            elif kind=="stumped":fp["stumpings"]+=1
            for pid,x in bat.items():
                p=ps[pid]; p["batting_innings"]+=1;p["runs"]+=x["runs"];p["balls_faced"]+=x["balls"];p["fours"]+=x["fours"];p["sixes"]+=x["sixes"]; dismissed=pid in outs
                if dismissed:p["dismissals"]+=1
                if x["runs"]>p["highest_score"]:p["highest_score"]=x["runs"];p["highest_score_not_out"]=not dismissed
                elif x["runs"]==p["highest_score"] and not dismissed:p["highest_score_not_out"]=True
                if 50<=x["runs"]<100:p["fifties"]+=1
                if x["runs"]>=100:p["hundreds"]+=1
            for pid,x in bowl.items():
                p=ps[pid];p["bowling_innings"]+=1;p["bowling_balls"]+=x["balls"];p["runs_conceded"]+=x["runs"];p["wickets"]+=x["wickets"]
                if x["wickets"]>=4:p["four_wicket_hauls"]+=1
                if x["wickets"]>=5:p["five_wicket_hauls"]+=1
                if x["wickets"]>p["best_bowling_wickets"]:p["best_bowling_wickets"]=x["wickets"];p["best_bowling_runs"]=x["runs"]
                elif x["wickets"]==p["best_bowling_wickets"] and x["wickets"]>0 and (p["best_bowling_runs"] is None or x["runs"]<p["best_bowling_runs"]):p["best_bowling_runs"]=x["runs"]
        if n%50==0 or n==len(files):print(f"{fmt.upper()}: {n}/{len(files)} matches")
    return ps

def stats(p):
    bi,d,bf,bb,w=p["batting_innings"],p["dismissals"],p["balls_faced"],p["bowling_balls"],p["wickets"]
    return {**{k:p[k] for k in ["matches","batting_innings","runs","balls_faced","fours","sixes","dismissals","fifties","hundreds","highest_score","highest_score_not_out","bowling_innings","bowling_balls","runs_conceded","wickets","four_wicket_hauls","five_wicket_hauls","best_bowling_wickets","catches","run_outs","stumpings"]},"not_outs":bi-d,"best_bowling_runs":p["best_bowling_runs"] or 0,"batting_average":round(p["runs"]/d if d else 0,2),"strike_rate":round(p["runs"]/bf*100 if bf else 0,2),"bowling_average":round(p["runs_conceded"]/w if w else 0,2),"economy":round(p["runs_conceded"]/bb*6 if bb else 0,2),"bowling_strike_rate":round(bb/w if w else 0,2),"overs":f"{bb//6}.{bb%6}"}

def similarity(ps):
    rows=[]
    for p in ps.values():
        m=p["matches"];bi=p["batting_innings"];d=p["dismissals"];bf=p["balls_faced"];bb=p["bowling_balls"];w=p["wickets"]
        ba=p["runs"]/d if d else 0;sr=p["runs"]/bf*100 if bf else 0;avg=p["runs"]/bi if bi else 0
        rows.append({"player_id":p["player_id"],"name":p["name"],"matches":m,"batting_average":ba,"strike_rate":sr,"runs_per_innings":avg,"fours_per_innings":p["fours"]/bi if bi else 0,"sixes_per_innings":p["sixes"]/bi if bi else 0,"fifties_per_innings":p["fifties"]/bi if bi else 0,"hundreds_per_innings":p["hundreds"]/bi if bi else 0,"highest_score":p["highest_score"],"wickets_per_match":w/m if m else 0,"bowling_average":p["runs_conceded"]/w if w else 0,"economy":p["runs_conceded"]/bb*6 if bb else 0,"catches_per_match":p["catches"]/m if m else 0,"run_outs_per_match":p["run_outs"]/m if m else 0,"stumpings_per_match":p["stumpings"]/m if m else 0})
    df=pd.DataFrame(rows);df=df[(df.matches>0)&((df.batting_average>0)|(df.wickets_per_match>0)|(df.catches_per_match>0))].copy()
    if df.empty:return {}
    X=StandardScaler().fit_transform(df[FEATURES].fillna(0))*WEIGHTS;S=cosine_similarity(X);ids=df.player_id.tolist();names=df.name.tolist();out={}
    for i,pid in enumerate(ids):
        order=sorted((j for j in range(len(ids)) if j!=i),key=lambda j:S[i,j],reverse=True)[:5]
        out[pid]=[{"player_id":ids[j],"name":names[j],"similarity":round(max(0,min(100,float(S[i,j])*100)),2)} for j in order]
    return out

def save(name,data):
    path=os.path.join(OUT,name)
    with open(path,"w",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,separators=(",",":"))
    print(f"Saved {path} ({os.path.getsize(path)/(1024*1024):.2f} MB)")

def main():
    os.makedirs(OUT,exist_ok=True);save("players.json",player_index())
    for fmt in ("test","odi","t20i"):
        ps=aggregate(fmt);save(f"stats_{fmt}.json",{pid:stats(p) for pid,p in ps.items()});save(f"similar_{fmt}.json",similarity(ps))
    print("DONE - frontend/data is ready")

if __name__=="__main__":main()
