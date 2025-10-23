﻿#include <iostream>
#include <fstream>
#include "VzenseNebula_api.h"
#include <thread>

using namespace std;
VzDeviceInfo* pDeviceListInfo = NULL;
VzDeviceHandle deviceHandle = 0;


bool InitDevice(const int deviceCount);
void HotPlugStateCallback(const VzDeviceInfo *pInfo, int status, void *contex);

int main(int argc, char *argv[])
{
	uint32_t deviceCount = 0;

	VzReturnStatus status = VZ_Initialize();
	if (status != VzReturnStatus::VzRetOK)
	{
		cout << "VzInitialize failed status:" <<status << endl;
		system("pause");
		return -1;
	}

GET:
	status = VZ_GetDeviceCount(&deviceCount);
	if (status != VzReturnStatus::VzRetOK)
	{
		cout << "VzGetDeviceCount failed status:" <<status << endl;
		system("pause");
		return -1;
	}
	cout << "Get device count: " << deviceCount << endl;
	if (0 == deviceCount)
	{
		this_thread::sleep_for(chrono::seconds(1));
		goto GET;
	}

	if (InitDevice(deviceCount))
	{
		status = VZ_SetHotPlugStatusCallback(HotPlugStateCallback, nullptr);;
		if (status != VzReturnStatus::VzRetOK)
		{
			cout << "SetHotPlugStatusCallback failed status:" <<status << endl;
 		}
		else
		{
			cout <<" wait for hotplug operation "<<endl;
			// wait for hotplug
			for (;;)
			{	
				this_thread::sleep_for(chrono::seconds(1));
			}
		}
		status = VZ_CloseDevice(&deviceHandle);
		if (status != VzReturnStatus::VzRetOK)
		{
			cout << "CloseDevice failed status:" <<status << endl;
		}
	}
	status = VZ_Shutdown();
	if (status != VzReturnStatus::VzRetOK)
	{
		cout << "Shutdown failed status:" <<status << endl;
	} 
 
	delete[] pDeviceListInfo;
	pDeviceListInfo = NULL;

	return 0;
}

bool InitDevice(const int deviceCount)
{
	if (pDeviceListInfo)
	{
		delete[] pDeviceListInfo;
		pDeviceListInfo = NULL;

	}

	pDeviceListInfo = new VzDeviceInfo[deviceCount];
	VzReturnStatus status = VZ_GetDeviceInfoList(deviceCount, pDeviceListInfo);
	if (status != VzReturnStatus::VzRetOK)
	{
		cout << "GetDeviceListInfo failed status:" << status << endl;
		return false;
	}
	else
	{
		if (VzConnected != pDeviceListInfo[0].status)
		{
			cout << "connect statu" << pDeviceListInfo[0].status << endl;
			cout << "Call VZ_OpenDevice with connect status :" << VzConnected << endl;
			return false;
		}
	}
	
	cout << "uri:" << pDeviceListInfo[0].uri << endl
	<< "alias:" << pDeviceListInfo[0].alias << endl
	<< "ip:" << pDeviceListInfo[0].ip << endl
	<< "connectStatus:" << pDeviceListInfo[0].status << endl;

	deviceHandle = 0;

	status = VZ_OpenDeviceByUri(pDeviceListInfo[0].uri, &deviceHandle);

	if (status != VzReturnStatus::VzRetOK)
	{
		cout << "OpenDevice failed status:" <<status << endl;
		return false;
	}

    cout << "open device successful,status :" << status << endl;

	status = VZ_StartStream(deviceHandle);

	if (status != VzReturnStatus::VzRetOK)
	{
		cout << "StartStream failed status:" <<status << endl;
		return false;
	}

	return true;
}

void HotPlugStateCallback(const VzDeviceInfo *pInfo, int status, void *contex)
{
	cout << "uri " << status << "  " << pInfo->uri << "    " << (status == 0 ? "add" : "remove") << endl;
	cout << "alias " << status << "  " << pInfo->alias << "    " << (status == 0 ? "add" : "remove") << endl;

	if (status == 0)
	{
		cout << "VZ_OpenDevice " << VZ_OpenDeviceByUri(pInfo->uri, &deviceHandle) << endl;
		cout << "VZ_StartStream " << VZ_StartStream(deviceHandle) << endl;
	}
	else
	{
		cout << "VZ_StopStream " << VZ_StopStream(deviceHandle) << endl;
		cout << "VZ_CloseDevice " << VZ_CloseDevice(&deviceHandle) << endl;
	}
}
