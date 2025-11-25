// Code generated for educational purposes
// Simplified Protobuf implementation for UserApps

package appsinstalled

import (
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/runtime/protoimpl"
)

// UserApps represents installed apps data for a user
type UserApps struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Apps []uint32 `protobuf:"varint,1,rep,name=apps" json:"apps,omitempty"`
	Lat  *float64 `protobuf:"fixed64,2,opt,name=lat" json:"lat,omitempty"`
	Lon  *float64 `protobuf:"fixed64,3,opt,name=lon" json:"lon,omitempty"`
}

func (x *UserApps) Reset() {
	*x = UserApps{}
}

func (x *UserApps) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*UserApps) ProtoMessage() {}

func (x *UserApps) ProtoReflect() protoreflect.Message {
	return nil // Simplified version
}

func (x *UserApps) GetApps() []uint32 {
	if x != nil {
		return x.Apps
	}
	return nil
}

func (x *UserApps) GetLat() float64 {
	if x != nil && x.Lat != nil {
		return *x.Lat
	}
	return 0
}

func (x *UserApps) GetLon() float64 {
	if x != nil && x.Lon != nil {
		return *x.Lon
	}
	return 0
}

// Helper function to create UserApps
func NewUserApps(apps []uint32, lat, lon float64) *UserApps {
	return &UserApps{
		Apps: apps,
		Lat:  &lat,
		Lon:  &lon,
	}
}

// Serialize UserApps to bytes using proto.Marshal
func (x *UserApps) Serialize() ([]byte, error) {
	return proto.Marshal(x)
}
