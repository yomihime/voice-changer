import React, { useEffect } from "react";
import { useGuiState } from "../001_GuiStateProvider";
import { QualityArea } from "./102-1_QualityArea";
import { ConvertArea } from "./102-2_ConvertArea";
import { DeviceArea } from "./102-3_DeviceArea";
import { RecorderArea } from "./102-4_RecorderArea";
import { MoreActionArea } from "./102-5_MoreActionArea";

export type ConfigAreaProps = {
    detectors: string[];
    inputChunkNums: number[];
};

export const ConfigArea = (props: ConfigAreaProps) => {
    const { showDeviceSettings, setShowDeviceSettings } = useGuiState();
    useEffect(() => {
        if (!showDeviceSettings) return;
        const closeOnEscape = (event: KeyboardEvent) => {
            if (event.key === "Escape") setShowDeviceSettings(false);
        };
        window.addEventListener("keydown", closeOnEscape);
        return () => window.removeEventListener("keydown", closeOnEscape);
    }, [showDeviceSettings, setShowDeviceSettings]);

    return (
        <>
            <div className="config-area vc-conversion-settings">
                <QualityArea detectors={props.detectors}></QualityArea>
                <ConvertArea inputChunkNums={props.inputChunkNums}></ConvertArea>
            </div>
            <div className="config-area vc-recorder-settings" id="vc-recorder">
                <RecorderArea></RecorderArea>
            </div>
            <div className="config-area vc-more-actions">
                <MoreActionArea></MoreActionArea>
            </div>
            <div
                className="vc-settings-overlay"
                hidden={!showDeviceSettings}
                onClick={(event) => {
                    if (event.target === event.currentTarget) setShowDeviceSettings(false);
                }}
            >
                <div className="vc-settings-modal" role="dialog" aria-modal="true" aria-labelledby="vc-settings-title">
                    <div className="vc-settings-title-row">
                        <h2 id="vc-settings-title">设置</h2>
                        <button type="button" aria-label="关闭设置" onClick={() => setShowDeviceSettings(false)}>
                            ×
                        </button>
                    </div>
                    <div className="config-area vc-device-settings" id="vc-device-settings">
                        <h3>音频设备设置</h3>
                        <DeviceArea></DeviceArea>
                    </div>
                </div>
            </div>
        </>
    );
};
