import * as T from '/vendor/three.module.js';
const shots={
 house:[[7.9,7.6,16.5],[0,3.55,.05],30,-165],
 relay:[[4.2,5.65,10.3],[.02,3.49,.25],28,-194],
 join:[[3.5,7.88,9.34],[.70,5.55,.22],27,-168],
 data:[[5.4,6.1,14.65],[0,3.56,.25],31,-163],
 ack:[[3.0,5.8,14.48],[0,3.54,.25],31,-156],
 internet:[[6.1,7.12,16.6],[.60,3.58,.12],30,-140],
 slots:[[4.6,6.4,15.8],[0,3.58,.12],30,-165],
 af:[[-16.45,3.44,10.43],[-18,1.27,.12],28,-163],
 df:[[-16.75,3.11,10.52],[-18,1.27,.12],28,-163],
 bench:[[19.95,3.94,8.85],[17.15,.99,.10],28,-134],
 end:[[8.4,7.8,17.2],[0,3.45,0],30,-162]
};
export function aim(cam,id,p,t){
 const [eye,look,fov,offset]=shots[id];const orbit=Math.sin((p-.45)*1.35)*.80;
 const target=new T.Vector3(...look);cam.position.set(eye[0]+orbit,eye[1]+Math.sin(p*2.0)*.12,eye[2]-.40*p);
 cam.fov=fov;cam.setViewOffset(1440,810,offset,0,1440,810);cam.lookAt(target);cam.updateProjectionMatrix();cam.updateMatrixWorld();
}
