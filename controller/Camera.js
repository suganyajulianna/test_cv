const CamereModel = require('../model/CamereSchema');
module.exports = {
    CameraPost: async (req, res) => {
        console.log('Received request body:', req.body);
        try {

          const {
            UserName,
            Password,
            CameraDetails,
            CameraLocationName,
            CameraLocationID,
            LocationDescription,
            IPAddress,
            Port,
            RTSPandRTMP,
            CamereVisibility
          } = req.body;

      
          const CameraData = new CamereModel({
            UserName:UserName,
            Password:Password,
            CameraDetails:CameraDetails,
            CameraLocationName:CameraLocationName,
            CameraLocationID:CameraLocationID,
            LocationDescription:LocationDescription,
            IPAddress:IPAddress,
            Port:Port,
            RTSPandRTMP:RTSPandRTMP,
            CameraVisibility:CamereVisibility

          });
      
          console.log('CameraData to be saved:', CameraData); 
      
          await CameraData.save();
          return res.status(200).json({ message: 'Successfully Registered' });
        } catch (error) {
          console.error('Error saving camera data:', error);  // Log the error
          return res.status(500).json({ message: 'Internal Server Error', error: error.message });
        }
      },
      
      
    CamereGet: async (req,res) =>{
       try{
        const data =  await CamereModel.find();
           return res.status(200).json({message:'Succesfully Got',data})
       }catch(err){
        return res.status(500).json({err:'Internal Server Error'})
       }
    },
    CamereUpdate: async (req,res)=>{
        try{
            const {id} = req.params;
            const data = req.body;
            const UpdateData = await CamereModel.findByIdAndUpfdate(id,data,{new:true});
            return res.status(200).json({message:'Succesfully Updated',UpdateData})
        }catch(err){
            return res.status(500).json({err:'Internal Server Error'})
        }
    },
    CamereDelete: async(req,res)=>{
        try{
            await CamereModel.findByIdAndDelete(req.params.id);
            return res.status(200).json({message:'Succesfully Deleted'})
        }catch(error){
            return res.status(500).json({err:'Internal Server Error'})
        }
    }
}